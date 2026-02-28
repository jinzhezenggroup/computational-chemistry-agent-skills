#!/usr/bin/env python3
"""
Generate/update README skills summary table from tools/**/SKILL.md.

Outputs a managed block in README.md between:
- <!-- SKILLS_TABLE_START -->
- <!-- SKILLS_TABLE_END -->
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
TOOLS_DIR = ROOT / "tools"

START_MARK = "<!-- SKILLS_TABLE_START -->"
END_MARK = "<!-- SKILLS_TABLE_END -->"


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


def collect_skills() -> list[SkillMeta]:
    rows: list[SkillMeta] = []
    for skill_file in sorted(TOOLS_DIR.glob("**/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_front_matter(text)

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


def update_readme(content: str, table: str) -> str:
    block = (
        f"{START_MARK}\n"
        "## Skills Summary\n\n"
        "Auto-generated from `tools/**/SKILL.md`.\n\n"
        f"{table}\n"
        f"{END_MARK}"
    )

    pattern = re.compile(rf"{re.escape(START_MARK)}.*?{re.escape(END_MARK)}", re.S)
    if pattern.search(content):
        return pattern.sub(block, content)

    if not content.endswith("\n"):
        content += "\n"
    return content + "\n" + block + "\n"


def main() -> int:
    rows = collect_skills()
    table = build_table(rows)

    readme_text = README.read_text(encoding="utf-8", errors="replace") if README.exists() else "# Skills\n"
    updated = update_readme(readme_text, table)
    README.write_text(updated, encoding="utf-8")

    print(f"Updated {README} with {len(rows)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
