#!/usr/bin/env python3
"""Validate SKILL.md YAML frontmatter using a JSON Schema.

This repo uses AgentSkills-style SKILL.md files. The frontmatter is YAML; we
parse it, then validate the resulting mapping against a JSON schema.

Designed for use in pre-commit.

Exit code:
- 0 if all files are valid
- 1 if any validation fails
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jsonschema
import yaml


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


def load_schema(schema_path: Path) -> dict:
    try:
        return schema_path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"cannot read schema: {schema_path}: {e}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--schema",
        default=str(Path("schemas") / "skill-frontmatter.schema.json"),
        help="Path to JSON schema file",
    )
    p.add_argument("paths", nargs="*", help="SKILL.md files to validate")
    args = p.parse_args(argv)

    schema_path = Path(args.schema)
    try:
        import json

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[schema] failed to load {schema_path}: {e}")
        return 1

    files = [Path(x) for x in args.paths] if args.paths else []
    if not files:
        files = list(Path.cwd().rglob("SKILL.md"))

    ok = True
    validator = jsonschema.Draft202012Validator(schema)

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

        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errors:
            ok = False
            for e in errors:
                loc = ".".join(str(x) for x in e.path) if e.path else "<root>"
                print(f"{f}: {loc}: {e.message}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
