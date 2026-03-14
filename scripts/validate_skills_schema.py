#!/usr/bin/env python3
"""Validate SKILL.md YAML frontmatter.

Design goals:
- Works in CI without extra pip installs by default (only uses stdlib)
- Can optionally validate against a JSON Schema if `jsonschema` is available

Validation rules:
- Parse YAML frontmatter by a minimal parser (no PyYAML dependency)
- Enforce AgentSkills core constraints (name/description)
- `metadata` is optional and may be a YAML mapping or a string

If `jsonschema` is importable and `schemas/skill-frontmatter.schema.json` exists,
we validate the parsed frontmatter dict against the schema (best-effort).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

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


def _parse_scalar(raw: str):
    s = raw.strip()
    if not s:
        return ""
    if s in {"true", "True"}:
        return True
    if s in {"false", "False"}:
        return False
    if s in {"null", "Null", "~"}:
        return None
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1]
    # very small int/float support
    try:
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        if re.fullmatch(r"-?\d+\.\d+", s):
            return float(s)
    except Exception:
        pass
    return s


def parse_yaml_minimal(front: str) -> dict:
    """Parse a small subset of YAML sufficient for this repo's frontmatter.

    Supported:
    - top-level key: value scalars
    - one-level nested mapping via indentation (e.g. metadata: \n  author: x)
    - ignores blank lines and comments

    Not a general YAML parser.
    """

    data: dict = {}
    cur_map_key: str | None = None
    cur_map: dict | None = None

    for raw in front.splitlines():
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        # nested: two-space indentation
        if line.startswith("  ") and cur_map is not None and cur_map_key is not None:
            nested = line.strip()
            if ":" not in nested:
                raise ValueError(f"invalid nested YAML line: {line!r}")
            k, v = nested.split(":", 1)
            cur_map[k.strip()] = _parse_scalar(v)
            continue

        # reset nesting
        cur_map_key = None
        cur_map = None

        if ":" not in line:
            raise ValueError(f"invalid YAML line (expected key: value): {line!r}")
        key, val = line.split(":", 1)
        key = key.strip()
        val_str = val.strip()

        # start nested map
        if val_str == "":
            cur_map_key = key
            cur_map = {}
            data[key] = cur_map
            continue

        data[key] = _parse_scalar(val_str)

    return data


def validate_frontmatter(data: dict) -> list[str]:
    errs: list[str] = []

    name = data.get("name")
    desc = data.get("description")

    if not isinstance(name, str) or not name.strip():
        errs.append("missing/invalid required key: name")
    else:
        if len(name) > 64:
            errs.append("name too long: maxLength=64")
        if not NAME_RE.match(name):
            errs.append("invalid name: must match ^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$")

    if not isinstance(desc, str) or not desc.strip():
        errs.append("missing/invalid required key: description")
    else:
        if len(desc) > 1024:
            errs.append("description too long: maxLength=1024")

    comp = data.get("compatibility")
    if comp is not None:
        if not isinstance(comp, str) or not comp.strip():
            errs.append("compatibility must be a non-empty string")
        elif len(comp) > 500:
            errs.append("compatibility too long: maxLength=500")

    meta = data.get("metadata")
    if meta is not None and not isinstance(meta, (dict, str)):
        errs.append("metadata must be a mapping (YAML object) or a string")

    allowed = data.get("allowed-tools")
    if allowed is not None and (not isinstance(allowed, str) or not allowed.strip()):
        errs.append("allowed-tools must be a non-empty string")

    lic = data.get("license")
    if lic is not None and (not isinstance(lic, str) or not lic.strip()):
        errs.append("license must be a non-empty string")

    return errs


def maybe_validate_jsonschema(data: dict, schema_path: Path) -> list[str]:
    try:
        import jsonschema  # type: ignore

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        out: list[str] = []
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            loc = ".".join(str(x) for x in e.path) if e.path else "<root>"
            out.append(f"{loc}: {e.message}")
        return out
    except ModuleNotFoundError:
        return []
    except Exception as e:
        # best-effort; do not fail due to schema engine issues
        return [f"[schema] validator error (ignored): {e}"]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="*", help="SKILL.md files to validate")
    p.add_argument(
        "--schema",
        default=str(Path("schemas") / "skill-frontmatter.schema.json"),
        help="Optional JSON schema path (validated only if jsonschema is installed)",
    )
    args = p.parse_args(argv)

    files = [Path(x) for x in args.paths] if args.paths else []
    if not files:
        files = list(Path.cwd().rglob("SKILL.md"))

    schema_path = Path(args.schema)

    ok = True
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            front = extract_frontmatter(text)
            data = parse_yaml_minimal(front)
        except Exception as e:
            ok = False
            print(f"{f}: {e}")
            continue

        errs = validate_frontmatter(data)
        if schema_path.exists():
            errs.extend(maybe_validate_jsonschema(data, schema_path))

        if errs:
            ok = False
            for e in errs:
                print(f"{f}: {e}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
