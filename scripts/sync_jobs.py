#!/usr/bin/env python3
"""
Git-native path sync (commit-by-commit) driven by sync.toml + sync-state.toml.

Flow per job:
1. Resolve target upstream revision (latest tag by regex or configured ref)
2. Read last synced upstream commit from sync-state.toml
3. List upstream commits touching `path` in (last, target]
4. For each commit, materialize snapshot of that path and commit into destination repo
5. Update sync-state.toml

This creates one destination commit per upstream commit (方案1).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import tomllib


ROOT = Path(__file__).resolve().parents[1]
SYNC_TOML = ROOT / "sync.toml"
STATE_TOML = ROOT / "sync-state.toml"


@dataclass
class Job:
    name: str
    enabled: bool
    upstream_repo: str
    upstream_ref: str
    path: str
    dest: str
    tag_regex: str | None


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    p = run(["git", *cmd], cwd=cwd, check=check)
    return p.stdout.strip()


def load_jobs() -> list[Job]:
    if not SYNC_TOML.exists():
        raise SystemExit(f"Missing {SYNC_TOML}")
    data = tomllib.loads(SYNC_TOML.read_text(encoding="utf-8"))
    rows = data.get("jobs", [])
    jobs: list[Job] = []
    for row in rows:
        jobs.append(
            Job(
                name=str(row["name"]),
                enabled=bool(row.get("enabled", True)),
                upstream_repo=str(row["upstream_repo"]),
                upstream_ref=str(row.get("upstream_ref", "master")),
                path=str(row["path"]).strip("/"),
                dest=str(row["dest"]).strip("/"),
                tag_regex=str(row.get("tag_regex")) if row.get("tag_regex") else None,
            )
        )
    return jobs


def load_state() -> dict[str, dict[str, Any]]:
    if not STATE_TOML.exists():
        return {"jobs": {}}
    data = tomllib.loads(STATE_TOML.read_text(encoding="utf-8"))
    if "jobs" not in data or not isinstance(data["jobs"], dict):
        return {"jobs": {}}
    return {"jobs": dict(data["jobs"])}


def dumps_toml(obj: dict[str, Any]) -> str:
    # Minimal TOML writer for our constrained structure.
    out: list[str] = ["version = 1", "", "[jobs]"]
    jobs = obj.get("jobs", {})
    for name in sorted(jobs.keys()):
        meta = jobs[name] or {}
        out.append(f"[jobs.\"{name}\"]")
        for k in ["last_upstream_commit", "last_upstream_ref", "updated_at"]:
            v = meta.get(k, "")
            esc = str(v).replace("\\", "\\\\").replace("\"", "\\\"")
            out.append(f"{k} = \"{esc}\"")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def save_state(state: dict[str, dict[str, Any]]) -> None:
    STATE_TOML.write_text(dumps_toml(state), encoding="utf-8")


def latest_tag(repo_url: str, tag_regex: str) -> str:
    out = git(["ls-remote", "--tags", "--refs", repo_url])
    tags: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        ref = line.split()[1]
        tag = ref.removeprefix("refs/tags/")
        if re.match(tag_regex, tag):
            tags.append(tag)
    if not tags:
        raise SystemExit(f"No tag matching {tag_regex!r} in {repo_url}")

    def ver_key(s: str):
        return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]

    tags.sort(key=ver_key)
    return tags[-1]


def ensure_clean_worktree() -> None:
    st = git(["status", "--porcelain"], cwd=ROOT)
    if st.strip():
        raise SystemExit("Destination repo is dirty; aborting")


def rsync_snapshot(up_repo: Path, up_rev: str, src_path: str, dest_path: str) -> None:
    # Materialize source directory snapshot at up_rev into destination path.
    git(["checkout", "--force", up_rev], cwd=up_repo)
    src_abs = up_repo / src_path
    dest_abs = ROOT / dest_path

    dest_abs.parent.mkdir(parents=True, exist_ok=True)
    if dest_abs.exists():
        shutil.rmtree(dest_abs)

    if src_abs.exists():
        shutil.copytree(src_abs, dest_abs)


def commit_if_changed(msg: str, author_name: str, author_email: str, author_date: str) -> bool:
    git(["add", "-A"], cwd=ROOT)
    changed = git(["diff", "--cached", "--name-only"], cwd=ROOT)
    if not changed.strip():
        return False

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": author_date,
            "GIT_COMMITTER_NAME": "OpenClaw",
            "GIT_COMMITTER_EMAIL": "actions@github.com",
            "GIT_COMMITTER_DATE": author_date,
        }
    )
    p = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise SystemExit(f"git commit failed: {p.stderr}")
    return True


def list_commits_for_path(up_repo: Path, last_commit: str | None, target: str, path: str) -> list[str]:
    # Return oldest -> newest commits that touched path.
    if last_commit:
        code = run(["git", "merge-base", "--is-ancestor", last_commit, target], cwd=up_repo, check=False).returncode
        if code != 0:
            return []
        rev_range = f"{last_commit}..{target}"
    else:
        rev_range = target

    out = git(["log", "--reverse", "--format=%H", rev_range, "--", path], cwd=up_repo)
    return [x for x in out.splitlines() if x.strip()]


def commit_meta(up_repo: Path, sha: str) -> tuple[str, str, str, str]:
    fmt = "%an%x00%ae%x00%aI%x00%s"
    raw = git(["show", "-s", f"--format={fmt}", sha], cwd=up_repo)
    an, ae, ai, subject = raw.split("\x00", 3)
    return an, ae, ai, subject


def resolve_target_ref(job: Job) -> tuple[str, str]:
    repo_url = f"https://github.com/{job.upstream_repo}.git"
    if job.tag_regex:
        tag = latest_tag(repo_url, job.tag_regex)
        return tag, tag
    return job.upstream_ref, job.upstream_ref


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_job(job: Job, state: dict[str, dict[str, Any]], rev_override: str = "") -> int:
    if not job.enabled:
        print(f"[skip] {job.name}: disabled")
        return 0

    state_jobs = state.setdefault("jobs", {})
    prev = state_jobs.get(job.name, {}) or {}
    last_commit = (prev.get("last_upstream_commit") or "").strip() or None

    logical_ref, fetch_ref = (rev_override, rev_override) if rev_override else resolve_target_ref(job)
    print(f"[job] {job.name}: upstream={job.upstream_repo} ref={logical_ref} path={job.path} -> {job.dest}")

    with tempfile.TemporaryDirectory(prefix=f"sync-{job.name}-") as tmp:
        up = Path(tmp) / "upstream"
        git(["clone", "--no-tags", "--filter=blob:none", f"https://github.com/{job.upstream_repo}.git", str(up)])

        if job.tag_regex:
            git(["fetch", "--tags", "origin"], cwd=up)

        target_sha = git(["rev-parse", f"origin/{fetch_ref}"], cwd=up, check=False)
        if not target_sha:
            target_sha = git(["rev-parse", fetch_ref], cwd=up)

        commits = list_commits_for_path(up, last_commit, target_sha, job.path)

        # Baseline if first run (no state) OR history rewrite.
        needs_baseline = last_commit is None
        if last_commit:
            code = run(["git", "merge-base", "--is-ancestor", last_commit, target_sha], cwd=up, check=False).returncode
            if code != 0:
                needs_baseline = True

        made = 0
        if needs_baseline:
            rsync_snapshot(up, target_sha, job.path, job.dest)
            an, ae, ai, _ = commit_meta(up, target_sha)
            msg = (
                f"chore(sync): baseline {job.dest} from {job.upstream_repo}:{job.path}\n\n"
                f"Upstream-Ref: {logical_ref}\n"
                f"Upstream-Commit: {target_sha}\n"
                f"Authored by OpenClaw (model: gpt-5.3-codex)"
            )
            if commit_if_changed(msg, an, ae, ai):
                made += 1
            commits = []

        for sha in commits:
            rsync_snapshot(up, sha, job.path, job.dest)
            an, ae, ai, subject = commit_meta(up, sha)
            msg = (
                f"sync({job.name}): {subject}\n\n"
                f"Upstream-Ref: {logical_ref}\n"
                f"Upstream-Commit: {sha}\n"
                f"Authored by OpenClaw (model: gpt-5.3-codex)"
            )
            if commit_if_changed(msg, an, ae, ai):
                made += 1

        state_jobs[job.name] = {
            "last_upstream_commit": target_sha,
            "last_upstream_ref": logical_ref,
            "updated_at": now_iso(),
        }
        save_state(state)

        # Always persist state update if changed.
        state_rel = str(STATE_TOML.relative_to(ROOT))
        git(["add", state_rel], cwd=ROOT)
        if git(["diff", "--cached", "--name-only"], cwd=ROOT).strip():
            msg = (
                f"chore(sync): update state for {job.name}\n\n"
                f"Upstream-Ref: {logical_ref}\n"
                f"Upstream-Commit: {target_sha}\n"
                f"Authored by OpenClaw (model: gpt-5.3-codex)"
            )
            if commit_if_changed(msg, "OpenClaw", "actions@github.com", now_iso()):
                made += 1

        print(f"[done] {job.name}: commits={made}, target={target_sha}")
        return made


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="", help="Run one named job only")
    parser.add_argument("--rev", default="", help="Override upstream ref/tag/SHA for selected job(s)")
    args = parser.parse_args()

    ensure_clean_worktree()

    jobs = load_jobs()
    if args.job:
        jobs = [j for j in jobs if j.name == args.job]
        if not jobs:
            raise SystemExit(f"Job not found: {args.job}")

    state = load_state()
    total = 0
    for job in jobs:
        total += run_job(job, state, rev_override=args.rev.strip())

    print(f"Total commits created: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
