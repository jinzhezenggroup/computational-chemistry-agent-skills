#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Generate/update README skills summary table from tools/**/SKILL.md.

Outputs managed blocks in README.md between:
- <!-- SKILLS_BADGE_START --> and <!-- SKILLS_BADGE_END -->
- <!-- SKILLS_TABLE_START --> and <!-- SKILLS_TABLE_END -->
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

START_MARK = "<!-- SKILLS_TABLE_START -->"
END_MARK = "<!-- SKILLS_TABLE_END -->"
BADGE_START = "<!-- SKILLS_BADGE_START -->"
BADGE_END = "<!-- SKILLS_BADGE_END -->"
EXCLUDED_DIRS = {".github"}


@dataclass
class SkillMeta:
    name: str
    slug: str
    version: str
    description: str
    location: Path
    compatibility: str


def parse_front_matter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    raw = m.group(1)
    data = yaml.safe_load(raw) or {}
    return data if isinstance(data, dict) else {}


def normalize_compatibility(meta: dict) -> str:
    val = meta.get("compatibility")
    if isinstance(val, str) and val.strip():
        return val.strip()
    return "-"


def normalize_version(meta: dict) -> str:
    md = meta.get("metadata")
    if isinstance(md, dict):
        v = md.get("version")
        if v is not None and str(v).strip():
            return str(v).strip()
    return "-"


def is_catalog_hidden(meta: dict) -> bool:
    val = meta.get("catalog-hidden", False)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "on"}
    return False


def is_excluded(skill_file: Path) -> bool:
    rel_parts = skill_file.relative_to(ROOT).parts
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def collect_skills() -> list[SkillMeta]:
    rows: list[SkillMeta] = []
    for skill_file in sorted(ROOT.glob("**/SKILL.md")):
        if is_excluded(skill_file):
            continue

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_front_matter(text)
        if is_catalog_hidden(fm):
            continue

        name = str(fm.get("name") or skill_file.parent.name)
        slug = str(fm.get("slug") or skill_file.parent.name)
        version = normalize_version(fm)
        description = str(fm.get("description") or "").replace("\n", " ").strip()
        compatibility = normalize_compatibility(fm)

        rows.append(
            SkillMeta(
                name=name,
                slug=slug,
                version=version,
                description=description,
                location=skill_file,
                compatibility=compatibility,
            )
        )
    return rows


def build_table(rows: list[SkillMeta]) -> str:
    header = [
        "| Skill | Description | Version | Compatibility |",
        "|---|---|---|---|",
    ]
    body: list[str] = []
    for r in rows:
        rel = r.location.relative_to(ROOT).as_posix()
        skill_link = f"[{r.name}]({rel})"
        desc = r.description.replace("|", "\\|") or "-"
        ver = r.version.replace("|", "\\|")
        req = r.compatibility.replace("|", "\\|")
        body.append(f"| {skill_link} | {desc} | {ver} | {req} |")
    if not body:
        body = ["| - | - | - | - |"]
    return "\n".join(header + body)


def build_badge(rows: list[SkillMeta]) -> str:
    count = len(rows)
    return (
        "[![Skills]"
        f"(https://img.shields.io/badge/skills-{count}-blue?style=for-the-badge)]"
        "(#skills-summary)"
    )


def update_managed_block(
    content: str,
    *,
    start_mark: str,
    end_mark: str,
    body: str,
    heading: str | None = None,
    insert_after: str | None = None,
) -> str:
    block = body if not heading else f"{heading}\n\n{body}"
    wrapped = f"{start_mark}\n{block}\n{end_mark}"

    pattern = re.compile(rf"{re.escape(start_mark)}.*?{re.escape(end_mark)}", re.S)
    if pattern.search(content):
        return pattern.sub(wrapped, content)

    if insert_after and insert_after in content:
        return content.replace(insert_after, f"{insert_after}\n\n{wrapped}", 1)

    if not content.endswith("\n"):
        content += "\n"
    return content + "\n" + wrapped + "\n"


def update_readme(content: str, badge: str, table: str) -> str:
    content = update_managed_block(
        content,
        start_mark=BADGE_START,
        end_mark=BADGE_END,
        body=badge,
        insert_after=(
            "[![GitHub contributors]"
            "(https://img.shields.io/github/contributors/jinzhezenggroup/computational-chemistry-agent-skills?style=for-the-badge&logo=github)]"
            "(https://github.com/jinzhezenggroup/computational-chemistry-agent-skills/graphs/contributors)"
        ),
    )
    return update_managed_block(
        content,
        start_mark=START_MARK,
        end_mark=END_MARK,
        heading="## Skills Summary",
        body=table,
    )


def main() -> int:
    rows = collect_skills()
    badge = build_badge(rows)
    table = build_table(rows)

    readme_text = (
        README.read_text(encoding="utf-8", errors="replace")
        if README.exists()
        else "# Skills\n"
    )
    updated = update_readme(readme_text, badge, table)
    README.write_text(updated, encoding="utf-8")

    print(f"Updated {README} with {len(rows)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
