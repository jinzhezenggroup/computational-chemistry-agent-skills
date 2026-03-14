#!/usr/bin/env python3
"""Validate SKILL.md YAML frontmatter for OpenClaw AgentSkills.

Designed to be used as a pre-commit hook.

Rules (OpenClaw-compatible):
- SKILL.md must start with YAML frontmatter delimited by --- ... ---
- Required keys: name, description (both single-line scalars)
- Frontmatter must be "single-line keys only": no indented/nested YAML mappings.
- If metadata is present, it must be a single-line JSON object (string) that parses to a dict.

You can relax some checks via flags.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

FRONTMATTER_START = "---"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$")


def extract_frontmatter(text: str, path: Path) -> tuple[str, str]:
    if not text.startswith(FRONTMATTER_START + "\n") and text.strip() != FRONTMATTER_START:
        raise ValueError("File must start with YAML frontmatter delimited by ---")

    # Find closing --- after the first line
    lines = text.splitlines(True)
    if not lines:
        raise ValueError("Empty file")
    if lines[0].strip() != FRONTMATTER_START:
        raise ValueError("First line must be ---")

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_START:
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("Missing closing --- for YAML frontmatter")

    front = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1 :])
    return front, body


def single_line_only(front: str) -> list[str]:
    """Return list of violations for OpenClaw 'single-line frontmatter keys only'."""
    problems: list[str] = []
    for n, raw in enumerate(front.splitlines(), start=1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # Disallow indentation (nested YAML) and list items
        if line.startswith(" ") or line.startswith("\t"):
            problems.append(f"frontmatter line {n}: indented YAML is not supported: {line!r}")
            continue
        if line.startswith("-"):
            problems.append(f"frontmatter line {n}: YAML lists are not supported: {line!r}")
            continue
        # Require key: value on same line
        if ":" not in line:
            problems.append(f"frontmatter line {n}: expected 'key: value' form: {line!r}")
            continue
        key, _ = line.split(":", 1)
        if not key.strip() or not re.match(r"^[A-Za-z0-9_-]+$", key.strip()):
            problems.append(f"frontmatter line {n}: invalid key name: {key!r}")
    return problems


def validate_file(path: Path, *, strict_openclaw: bool, require_metadata_keys: list[str]) -> list[str]:
    errs: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"cannot read: {e}"]

    try:
        front, _body = extract_frontmatter(text, path)
    except Exception as e:
        return [str(e)]

    if strict_openclaw:
        errs.extend(single_line_only(front))

    try:
        data = yaml.safe_load(front) or {}
    except Exception as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return ["frontmatter must parse to a mapping (YAML object)"]

    # Required: name, description
    name = data.get("name")
    desc = data.get("description")
    if not isinstance(name, str) or not name.strip():
        errs.append("missing/invalid required key: name")
    if not isinstance(desc, str) or not desc.strip():
        errs.append("missing/invalid required key: description")

    if isinstance(name, str):
        if not NAME_RE.match(name):
            errs.append(
                "invalid name: must be lowercase letters/digits/hyphens, length<=64 (recommended), got: "
                + repr(name)
            )

    # metadata: single-line JSON object (OpenClaw)
    if "metadata" in data:
        meta = data.get("metadata")
        if strict_openclaw:
            if not isinstance(meta, str):
                errs.append(
                    "metadata must be a single-line JSON object string for OpenClaw (e.g. metadata: {\"openclaw\":{...}})"
                )
            else:
                try:
                    meta_obj = json.loads(meta)
                except Exception as e:
                    errs.append(f"metadata JSON parse error: {e}")
                else:
                    if not isinstance(meta_obj, dict):
                        errs.append("metadata JSON must parse to an object (dict)")
                    else:
                        for k in require_metadata_keys:
                            if k not in meta_obj:
                                errs.append(f"metadata missing required key: {k}")
        else:
            # loose mode: allow YAML dict too
            if isinstance(meta, str):
                try:
                    meta_obj = json.loads(meta)
                except Exception:
                    meta_obj = None
                if meta_obj is not None and not isinstance(meta_obj, dict):
                    errs.append("metadata JSON must parse to an object (dict)")
            elif isinstance(meta, dict):
                for k in require_metadata_keys:
                    if k not in meta:
                        errs.append(f"metadata missing required key: {k}")
            else:
                errs.append("metadata must be either a JSON string or a YAML mapping")

    return errs


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*", help="SKILL.md files to validate")
    p.add_argument("--strict-openclaw", action="store_true", default=True)
    p.add_argument("--no-strict-openclaw", dest="strict_openclaw", action="store_false")
    p.add_argument(
        "--require-metadata-key",
        action="append",
        default=[],
        help="Require key in metadata object (repeatable). Example: --require-metadata-key author",
    )

    args = p.parse_args(argv)

    files = [Path(x) for x in args.paths] if args.paths else []
    # If pre-commit passes no files, scan from CWD.
    if not files:
        files = list(Path.cwd().rglob("SKILL.md"))

    all_ok = True
    for f in files:
        errs = validate_file(
            f,
            strict_openclaw=args.strict_openclaw,
            require_metadata_keys=args.require_metadata_key,
        )
        if errs:
            all_ok = False
            for e in errs:
                print(f"{f}: {e}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
