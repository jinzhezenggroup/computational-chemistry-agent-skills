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

Also preserves high-level categorization by directory. For a SKILL located at:
  tools/openbabel/SKILL.md
category will be:
  tools

Additionally generates per-skill zip files for download on the static site:
  - site/public/skill-zips/<slug>.zip

Each zip contains a single top-level folder equal to the skill directory name,
and includes the full contents of that skill directory (SKILL.md + any scripts/files).
"""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
OUT_JSON = SITE_DIR / "src" / "data" / "skills.json"
OUT_CONTENT_DIR = SITE_DIR / "src" / "content" / "skills"
OUT_ZIPS_DIR = SITE_DIR / "public" / "skill-zips"
EXCLUDED_DIRS = {".github"}


@dataclass
class Skill:
    name: str
    slug: str
    description: str
    compatibility: str
    version: str
    repository: str | None
    source_path: str
    category: str | None
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


def is_catalog_hidden(fm: dict) -> bool:
    val = fm.get("catalog-hidden", False)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"1", "true", "yes", "on"}
    return False


def derive_category(rel_path: str) -> str | None:
    # rel_path like "tools/openbabel/SKILL.md" or "molecular-dynamics/lammps-deepmd/SKILL.md"
    parts = rel_path.split("/")
    if len(parts) >= 2:
        return parts[0]
    return None


def is_excluded(skill_file: Path) -> bool:
    rel_parts = skill_file.relative_to(ROOT).parts
    return any(part in EXCLUDED_DIRS for part in rel_parts)


def collect() -> list[Skill]:
    rows: list[Skill] = []
    for p in sorted(ROOT.glob("**/SKILL.md")):
        if is_excluded(p):
            continue

        rel = p.relative_to(ROOT).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_front_matter(text)
        if is_catalog_hidden(fm):
            continue

        name = norm_str(fm.get("name"), p.parent.name)
        slug = norm_str(fm.get("slug"), p.parent.name)
        desc = norm_str(fm.get("description"), "")
        compat = norm_str(fm.get("compatibility"), "-")
        ver = get_version(fm)
        repo = get_repo(fm)
        category = derive_category(rel)

        rows.append(
            Skill(
                name=name,
                slug=slug,
                description=desc,
                compatibility=compat,
                version=ver,
                repository=repo,
                source_path=rel,
                category=category,
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
            "category": s.category,
        }
        for s in skills
    ]
    OUT_JSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Content collection markdown pages
    expected = {f"{s.slug}.md" for s in skills}
    for old in OUT_CONTENT_DIR.glob("*.md"):
        if old.name not in expected:
            old.unlink()

    for s in skills:
        out = OUT_CONTENT_DIR / f"{s.slug}.md"
        fm = {
            "name": s.name,
            "description": s.description,
            "compatibility": s.compatibility,
            "version": s.version,
            "repository": s.repository,
            "sourcePath": s.source_path,
            "category": s.category,
        }
        # remove null values for cleaner front matter
        fm = {k: v for k, v in fm.items() if v is not None}
        out.write_text(
            "---\n"
            + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
            + "\n---\n\n"
            + s.body,
            encoding="utf-8",
        )


def _iter_zip_files(skill_dir_abs: Path) -> list[Path]:
    """Return all files under skill_dir_abs to include in zip."""
    files: list[Path] = []
    for p in skill_dir_abs.rglob("*"):
        if p.is_dir():
            continue
        # Skip obvious junk if present
        if p.name in {".DS_Store"}:
            continue
        if "__pycache__" in p.parts:
            continue
        files.append(p)
    return files


def write_skill_zips(skills: list[Skill]) -> None:
    OUT_ZIPS_DIR.mkdir(parents=True, exist_ok=True)

    expected = {f"{s.slug}.zip" for s in skills}
    for old in OUT_ZIPS_DIR.glob("*.zip"):
        if old.name not in expected:
            old.unlink()

    for s in skills:
        # source_path is like tools/openbabel/SKILL.md
        skill_dir_rel = Path(s.source_path).parent
        skill_dir_abs = ROOT / skill_dir_rel
        install_folder_name = skill_dir_rel.name

        if not (skill_dir_abs / "SKILL.md").exists():
            raise FileNotFoundError(f"Expected SKILL.md under {skill_dir_abs}")

        out_zip = OUT_ZIPS_DIR / f"{s.slug}.zip"

        files = _iter_zip_files(skill_dir_abs)
        # Ensure deterministic output: fixed order
        files = sorted(files, key=lambda p: p.as_posix())

        with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                rel_in_skill = f.relative_to(skill_dir_abs).as_posix()
                arcname = f"{install_folder_name}/{rel_in_skill}"
                zf.write(f, arcname)


def main() -> int:
    skills = collect()
    write_outputs(skills)
    write_skill_zips(skills)
    print(f"Generated site data for {len(skills)} skills")
    print(f"Generated per-skill zips into {OUT_ZIPS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
