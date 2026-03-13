#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Generate static site data for the skills catalog.

- Scans **/SKILL.md
- Extracts YAML front matter
- Writes:
  - site/src/data/skills.json
  - site/src/content/skills/<slug>.md (generated)

The generated markdown files keep (most of) the original SKILL.md body content,
with a normalized front matter schema for Astro Content Collections.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
OUT_JSON = SITE_DIR / "src" / "data" / "skills.json"
OUT_CONTENT_DIR = SITE_DIR / "src" / "content" / "skills"


@dataclass
class Skill:
    name: str
    slug: str
    description: str
    compatibility: str
    version: str
    repository: str | None
    source_path: str
    body: str


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Return (front_matter_dict, body_markdown)."""
    if not text.startswith("---\n"):
        return {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    data = yaml.safe_load(fm_raw) or {}
    return (data if isinstance(data, dict) else {}), body


def norm_str(x: object, default: str = "") -> str:
    if x is None:
        return default
    s = str(x).strip()
    return s if s else default


def get_version(fm: dict) -> str:
    md = fm.get("metadata")
    if isinstance(md, dict) and md.get("version") is not None:
        return norm_str(md.get("version"), "-")
    return "-"


def get_repo(fm: dict) -> str | None:
    md = fm.get("metadata")
    if isinstance(md, dict):
        repo = md.get("repository")
        if repo:
            return norm_str(repo)
    repo = fm.get("repository")
    return norm_str(repo) if repo else None


def collect() -> list[Skill]:
    rows: list[Skill] = []
    for p in sorted(ROOT.glob("**/SKILL.md")):
        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_front_matter(text)

        name = norm_str(fm.get("name"), p.parent.name)
        slug = norm_str(fm.get("slug"), p.parent.name)
        desc = norm_str(fm.get("description"), "")
        compat = norm_str(fm.get("compatibility"), "-")
        ver = get_version(fm)
        repo = get_repo(fm)

        rows.append(
            Skill(
                name=name,
                slug=slug,
                description=desc,
                compatibility=compat,
                version=ver,
                repository=repo,
                source_path=rel,
                body=body.strip() + "\n",
            )
        )
    return rows


def write_outputs(skills: list[Skill]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # JSON for listing
    data = [
        {
            "name": s.name,
            "slug": s.slug,
            "description": s.description,
            "compatibility": s.compatibility,
            "version": s.version,
            "repository": s.repository,
            "sourcePath": s.source_path,
        }
        for s in skills
    ]
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Content collection markdown pages
    for s in skills:
        out = OUT_CONTENT_DIR / f"{s.slug}.md"
        fm = {
            "name": s.name,
            "description": s.description,
            "compatibility": s.compatibility,
            "version": s.version,
            "repository": s.repository,
            "sourcePath": s.source_path,
        }
        # remove null values for cleaner front matter
        fm = {k: v for k, v in fm.items() if v is not None}
        out.write_text(
            "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n\n" + s.body,
            encoding="utf-8",
        )


def main() -> int:
    skills = collect()
    write_outputs(skills)
    print(f"Generated site data for {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
