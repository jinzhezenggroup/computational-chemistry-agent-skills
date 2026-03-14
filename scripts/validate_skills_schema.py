#!/usr/bin/env python3
"""Validate SKILL.md YAML frontmatter.

This repo uses AgentSkills-style SKILL.md files. The frontmatter is YAML.

Validation strategy:
- Parse YAML frontmatter into a Python dict
- Validate required fields and naming constraints from AgentSkills spec

Notes:
- Do NOT require any OpenClaw-specific `metadata` encoding here; OpenClaw parses
  YAML frontmatter in practice and repo skills already use nested YAML maps.

Designed for use in pre-commit.

Exit code:
- 0 if all files are valid
- 1 if any validation fails
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$")


def extract_frontmatter(text: str) -> str:
    if not text.startswith("---\n") and text.strip() != "---":
        raise ValueError("File must start with YAML frontmatter delimited by ---")

    lines = text.splitlines(True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("First line must be ---")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("Missing closing --- for YAML frontmatter")

    return "".join(lines[1:end_idx])


def validate_frontmatter(data: dict, *, file_path: Path) -> list[str]:
    errs: list[str] = []

    # required: name, description
    name = data.get("name")
    desc = data.get("description")

    if not isinstance(name, str) or not name.strip():
        errs.append("missing/invalid required key: name")
    else:
        if len(name) > 64:
            errs.append("name too long: maxLength=64")
        if not NAME_RE.match(name):
            errs.append(
                "invalid name: must match ^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$"
            )

    if not isinstance(desc, str) or not desc.strip():
        errs.append("missing/invalid required key: description")
    else:
        if len(desc) > 1024:
            errs.append("description too long: maxLength=1024")

    # optional: compatibility
    comp = data.get("compatibility")
    if comp is not None:
        if not isinstance(comp, str) or not comp.strip():
            errs.append("compatibility must be a non-empty string")
        elif len(comp) > 500:
            errs.append("compatibility too long: maxLength=500")

    # optional: metadata
    meta = data.get("metadata")
    if meta is not None:
        if not isinstance(meta, (dict, str)):
            errs.append("metadata must be a mapping (YAML object) or a string")

    # optional: allowed-tools
    allowed = data.get("allowed-tools")
    if allowed is not None:
        if not isinstance(allowed, str) or not allowed.strip():
            errs.append("allowed-tools must be a non-empty string")

    # optional: license
    lic = data.get("license")
    if lic is not None:
        if not isinstance(lic, str) or not lic.strip():
            errs.append("license must be a non-empty string")

    return errs


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*", help="SKILL.md files to validate")
    args = p.parse_args(argv)

    files = [Path(x) for x in args.paths] if args.paths else []
    if not files:
        files = list(Path.cwd().rglob("SKILL.md"))

    ok = True

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            front = extract_frontmatter(text)
            data = yaml.safe_load(front) or {}
        except Exception as e:
            ok = False
            print(f"{f}: {e}")
            continue

        if not isinstance(data, dict):
            ok = False
            print(f"{f}: frontmatter must parse to a YAML mapping (object)")
            continue

        errs = validate_frontmatter(data, file_path=f)
        if errs:
            ok = False
            for e in errs:
                print(f"{f}: {e}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
