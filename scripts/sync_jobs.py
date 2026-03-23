#!/usr/bin/env python3
"""
Pure-git sync runner.

- Reads jobs from sync.toml
- Reads/writes last synced upstream commit in sync-state.toml
- For each job, replays upstream commits (that touched job.path) into job.dest
  as one destination commit per upstream commit (方案1)
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


def run(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    p = run(["git", *args], cwd=cwd, check=check)
    return p.stdout.strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_clean_worktree() -> None:
    if git(["status", "--porcelain"], cwd=ROOT).strip():
        raise SystemExit("Destination repo is dirty; aborting")


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
    jobs = data.get("jobs", {})
    if not isinstance(jobs, dict):
        jobs = {}
    return {"jobs": dict(jobs)}


def dump_state_toml(state: dict[str, dict[str, Any]]) -> str:
    out = ["version = 1", "", "[jobs]"]
    jobs = state.get("jobs", {})
    for name in sorted(jobs.keys()):
        meta = jobs[name] or {}
        out.append(f'[jobs."{name}"]')
        for k in ("last_upstream_commit", "last_upstream_ref", "updated_at"):
            v = str(meta.get(k, "")).replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'{k} = "{v}"')
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def save_state(state: dict[str, dict[str, Any]]) -> None:
    STATE_TOML.write_text(dump_state_toml(state), encoding="utf-8")


def rev_parse_commit(repo: Path, ref: str) -> str:
    p = run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo, check=False
    )
    return p.stdout.strip() if p.returncode == 0 else ""


def resolve_upstream_commit(up_repo: Path, ref: str) -> str:
    for cand in (f"origin/{ref}", f"refs/tags/{ref}", ref):
        sha = rev_parse_commit(up_repo, cand)
        if sha:
            return sha
    raise SystemExit(f"Cannot resolve upstream ref: {ref}")


def latest_matching_tag(repo_url: str, pattern: str) -> str:
    out = git(["ls-remote", "--tags", "--refs", repo_url])
    tags: list[str] = []
    for line in out.splitlines():
        ref = line.split()[1]
        tag = ref.removeprefix("refs/tags/")
        if re.match(pattern, tag):
            tags.append(tag)
    if not tags:
        raise SystemExit(f"No tag matches {pattern!r} in {repo_url}")

    def ver_key(s: str):
        return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]

    tags.sort(key=ver_key)
    return tags[-1]


def resolve_target_ref(job: Job, rev_override: str = "") -> str:
    if rev_override:
        return rev_override
    if job.tag_regex:
        repo_url = f"https://github.com/{job.upstream_repo}.git"
        return latest_matching_tag(repo_url, job.tag_regex)
    return job.upstream_ref


def list_commits_for_path(
    up_repo: Path, last_commit: str | None, target_sha: str, path: str
) -> list[str]:
    if last_commit:
        # If upstream rewrote history, degrade to one-shot baseline at target.
        anc = run(
            ["git", "merge-base", "--is-ancestor", last_commit, target_sha],
            cwd=up_repo,
            check=False,
        )
        if anc.returncode != 0:
            return [target_sha]
        rev_range = f"{last_commit}..{target_sha}"
    else:
        rev_range = target_sha

    out = git(["log", "--reverse", "--format=%H", rev_range, "--", path], cwd=up_repo)
    commits = [x for x in out.splitlines() if x.strip()]

    # If state exists but no path commit in range, nothing to replay.
    return commits


def commit_meta(up_repo: Path, sha: str) -> tuple[str, str, str, str]:
    raw = git(["show", "-s", "--format=%an%x00%ae%x00%aI%x00%s", sha], cwd=up_repo)
    an, ae, ai, subject = raw.split("\x00", 3)
    return an, ae, ai, subject


def checkout_snapshot(up_repo: Path, sha: str, src_path: str, dst_path: str) -> None:
    git(["checkout", "--force", sha], cwd=up_repo)
    src = up_repo / src_path
    dst = ROOT / dst_path

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    if src.exists():
        shutil.copytree(src, dst)


def path_exists_in_commit(up_repo: Path, sha: str, path: str) -> bool:
    p = run(["git", "cat-file", "-e", f"{sha}:{path}"], cwd=up_repo, check=False)
    return p.returncode == 0


def run_pre_commit() -> None:
    p = run(["uvx", "prek", "run", "-a"], cwd=ROOT, check=False)


def commit_if_changed(
    message: str, author_name: str, author_email: str, author_date: str
) -> bool:
    git(["add", "-A"], cwd=ROOT)
    if not git(["diff", "--cached", "--name-only"], cwd=ROOT).strip():
        return False

    run_pre_commit()
    git(["add", "-A"], cwd=ROOT)

    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": author_date,
            "GIT_COMMITTER_NAME": "GitHub Actions",
            "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
            "GIT_COMMITTER_DATE": author_date,
        }
    )
    p = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise SystemExit(f"git commit failed: {p.stderr}")
    return True


def run_job(job: Job, state: dict[str, dict[str, Any]], rev_override: str = "") -> int:
    if not job.enabled:
        print(f"[skip] {job.name}: disabled")
        return 0

    state_jobs = state.setdefault("jobs", {})
    prev = state_jobs.get(job.name, {}) or {}
    last_commit = (prev.get("last_upstream_commit") or "").strip() or None

    logical_ref = resolve_target_ref(job, rev_override=rev_override)
    print(
        f"[job] {job.name}: {job.upstream_repo}@{logical_ref}  {job.path} -> {job.dest}"
    )

    with tempfile.TemporaryDirectory(prefix=f"sync-{job.name}-") as tmp:
        up_repo = Path(tmp) / "upstream"
        git(
            [
                "clone",
                "--no-tags",
                f"https://github.com/{job.upstream_repo}.git",
                str(up_repo),
            ]
        )
        git(["fetch", "--tags", "origin"], cwd=up_repo)

        target_sha = resolve_upstream_commit(up_repo, logical_ref)

        # Fail fast: do not allow state-only updates for missing source path.
        if not path_exists_in_commit(up_repo, target_sha, job.path):
            raise SystemExit(
                f"Source path not found in upstream at {logical_ref} ({target_sha}): {job.path}"
            )

        commits = list_commits_for_path(up_repo, last_commit, target_sha, job.path)

        made = 0
        for sha in commits:
            checkout_snapshot(up_repo, sha, job.path, job.dest)
            an, ae, ai, subject = commit_meta(up_repo, sha)

            # Keep state in the same commit to avoid a noisy extra state-only commit.
            state_jobs[job.name] = {
                "last_upstream_commit": sha,
                "last_upstream_ref": logical_ref,
                "updated_at": now_iso(),
            }
            save_state(state)

            msg = (
                f"sync({job.name}): {subject}\n\n"
                f"Upstream-Ref: {logical_ref}\n"
                f"Upstream-Commit: {job.upstream_repo}@{sha}"
            )
            if commit_if_changed(msg, an, ae, ai):
                made += 1

        # If no replayed commit but state differs, write one state update commit.
        if made == 0:
            prev_commit = (prev.get("last_upstream_commit") or "").strip()
            prev_ref = (prev.get("last_upstream_ref") or "").strip()
            if prev_commit != target_sha or prev_ref != logical_ref:
                state_jobs[job.name] = {
                    "last_upstream_commit": target_sha,
                    "last_upstream_ref": logical_ref,
                    "updated_at": now_iso(),
                }
                save_state(state)

                msg = (
                    f"chore(sync): update state for {job.name}\n\n"
                    f"Upstream-Ref: {logical_ref}\n"
                    f"Upstream-Commit: {target_sha}"
                )
                if commit_if_changed(
                    msg,
                    "GitHub Actions",
                    "41898282+github-actions[bot]@users.noreply.github.com",
                    now_iso(),
                ):
                    made += 1

        print(f"[done] {job.name}: commits={made}, target={target_sha}")
        return made


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="", help="Run one named job only")
    parser.add_argument(
        "--rev", default="", help="Override upstream ref/tag/SHA for selected job(s)"
    )
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
