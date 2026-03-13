#!/usr/bin/env python3
"""End-to-end ReacNetGenerator runner for common LAMMPS trajectory cases.

Features
- Accept LAMMPS dump with x/y/z OR xs/ys/zs (scaled). For scaled coords, convert to x/y/z.
- Orthorhombic box only for conversion.
- Infer atomnames order from a LAMMPS data file (Masses) if atomnames not provided.
- Run via local `reacnetgenerator` or fallback to `uvx --from reacnetgenerator reacnetgenerator`.
- Write outputs into out/<basename>/ and keep logs.

Security / robustness
- Avoid shell=True; run subprocess with argv lists to prevent whitespace bugs and injection risks.
- If multiple .data candidates are present and selection is ambiguous:
  - default: stop and ask the user to specify --data
  - with --pick-data: prompt the user to choose interactively (TTY only)
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def detect_dump_coord_mode(dump_path: Path) -> str:
    """Return 'xyz' if ATOMS header contains x/y/z, 'scaled' if xs/ys/zs, else 'unknown'."""
    with dump_path.open("r", errors="replace") as f:
        for _ in range(2000):
            ln = f.readline()
            if not ln:
                break
            if ln.startswith("ITEM: ATOMS"):
                keys = ln.strip().split()[2:]
                if ("x" in keys) and ("y" in keys) and ("z" in keys):
                    return "xyz"
                if ("xs" in keys) and ("ys" in keys) and ("zs" in keys):
                    return "scaled"
                return "unknown"
    return "unknown"


def infer_max_type_from_dump_first_frame(dump_path: Path) -> int | None:
    """Read the first frame of a LAMMPS dump and return max numeric atom type seen.

    Requires an ATOMS header with a 'type' column.
    """
    with dump_path.open("r", errors="replace") as f:
        line = f.readline()
        if not line or not line.startswith("ITEM: TIMESTEP"):
            return None
        f.readline()  # timestep

        line = f.readline()
        if not line.startswith("ITEM: NUMBER OF ATOMS"):
            return None
        natoms_line = f.readline()
        if not natoms_line:
            return None
        try:
            natoms = int(natoms_line.strip())
        except Exception:
            return None

        line = f.readline()
        if not line.startswith("ITEM: BOX BOUNDS"):
            return None
        for _ in range(3):
            if not f.readline():
                return None

        line = f.readline()
        if not line.startswith("ITEM: ATOMS"):
            return None
        keys = line.strip().split()[2:]
        try:
            type_idx = keys.index("type")
        except ValueError:
            return None

        max_type = None
        for _ in range(natoms):
            ln = f.readline()
            if not ln:
                break
            parts = ln.split()
            if len(parts) <= type_idx:
                continue
            try:
                t = int(float(parts[type_idx]))
            except Exception:
                continue
            max_type = t if (max_type is None or t > max_type) else max_type

        return max_type


def parse_atom_types_count_from_data(data_path: Path) -> int | None:
    # Typical line: "4 atom types"
    text = data_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*(\d+)\s+atom\s+types\b", text, flags=re.MULTILINE | re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


@dataclass
class DataCandidate:
    path: Path
    atom_types: int | None
    mtime: float
    name_score: int
    type_match: bool


def score_name_similarity(stem: str, data_path: Path) -> int:
    # Very lightweight heuristic: prefer shared substrings.
    name = data_path.stem.lower()
    s = stem.lower()
    score = 0
    if name == s:
        score += 100
    if name.startswith(s) or s.startswith(name):
        score += 30
    toks_s = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    toks_n = [t for t in re.split(r"[^a-z0-9]+", name) if t]
    score += 5 * len(set(toks_s) & set(toks_n))
    return score


def _build_data_candidates(input_path: Path, hits: list[Path]) -> tuple[list[DataCandidate], int | None]:
    expected_types = None
    try:
        if detect_dump_coord_mode(input_path) in ("xyz", "scaled", "unknown"):
            expected_types = infer_max_type_from_dump_first_frame(input_path)
    except Exception:
        expected_types = None

    stem = input_path.stem
    cands: list[DataCandidate] = []
    for p in hits:
        atom_types = None
        try:
            atom_types = parse_atom_types_count_from_data(p)
        except Exception:
            atom_types = None
        mtime = p.stat().st_mtime
        name_score = score_name_similarity(stem, p)
        type_match = (expected_types is not None and atom_types is not None and atom_types == expected_types)
        cands.append(DataCandidate(p, atom_types, mtime, name_score, type_match))

    cands_sorted = sorted(
        cands,
        key=lambda c: (
            0 if c.type_match else 1,
            -c.name_score,
            -c.mtime,
            str(c.path),
        ),
    )
    return cands_sorted, expected_types


def _interactive_pick_data(cands_sorted: list[DataCandidate], expected_types: int | None) -> Path:
    if not sys.stdin.isatty():
        die("--pick-data requires an interactive TTY (stdin is not a TTY). Use --data to specify explicitly.")

    print("Multiple LAMMPS data files found. Please choose one:")
    if expected_types is not None:
        print(f"(Hint) inferred max atom type from dump: {expected_types}")

    for i, c in enumerate(cands_sorted, start=1):
        mark = "*" if c.type_match else " "
        print(f"[{i}] {mark} {c.path}  (atom_types={c.atom_types}, name_score={c.name_score})")

    while True:
        sel = input(f"Select 1-{len(cands_sorted)} (or 'q' to quit): ").strip().lower()
        if sel in ("q", "quit", "exit"):
            die("Aborted by user.")
        try:
            idx = int(sel)
        except Exception:
            print("Invalid input. Enter a number.")
            continue
        if 1 <= idx <= len(cands_sorted):
            return cands_sorted[idx - 1].path
        print("Out of range.")


def choose_data_file(
    input_path: Path,
    user_data: str | None,
    *,
    pick_data: bool,
    dry_run: bool,
) -> Path | None:
    """Choose a LAMMPS data file.

    - If user_data is provided, use it (must exist).
    - Otherwise search same directory for *.data (and a few common extensions).
    - If multiple candidates:
        * Prefer ones whose "N atom types" matches the max type observed in the dump's first frame.
        * Break ties by name similarity, then mtime.
      If still ambiguous:
        - If pick_data: prompt user to choose interactively (unless dry-run)
        - Else: stop and ask the user to pass --data
    """
    if user_data:
        p = Path(user_data).expanduser().resolve()
        return p if p.exists() else None

    patterns = ("*.data", "*.lmp", "*.lammps")
    hits: list[Path] = []
    for pat in patterns:
        hits.extend(sorted(input_path.parent.glob(pat)))
    hits = sorted(set(hits))
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]

    cands_sorted, expected_types = _build_data_candidates(input_path, hits)

    # If user wants interactive selection, do it unless dry-run.
    if pick_data and not dry_run:
        return _interactive_pick_data(cands_sorted, expected_types)

    # Otherwise: pick best, but if ambiguous, stop (unless dry-run where we just show info).
    best = cands_sorted[0]
    top_group = [c for c in cands_sorted if c.type_match == best.type_match and c.name_score == best.name_score]
    ambiguous = (len(top_group) > 1 and best.name_score < 100)

    if ambiguous:
        lines = ["Multiple LAMMPS data files found; please specify --data explicitly (or re-run with --pick-data):"]
        if expected_types is not None:
            lines.append(f"- inferred max atom type from dump: {expected_types}")
        for c in cands_sorted:
            lines.append(
                f"- {c.path} (atom_types={c.atom_types}, type_match={c.type_match}, name_score={c.name_score})"
            )
        if dry_run:
            print("\n".join(lines))
            print(f"[plan] would choose: {best.path}")
            return best.path
        die("\n".join(lines))

    return best.path


def run_argv(argv: list[str], log_path: Path, cwd: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        p = subprocess.Popen(argv, cwd=str(cwd), stdout=log, stderr=subprocess.STDOUT, text=True)
        code = p.wait()
    if code != 0:
        die(f"Command failed ({code}). See log: {log_path}")


def argv_to_pretty(argv: Iterable[str]) -> str:
    def q(s: str) -> str:
        if re.search(r"[\s'\"\\$`!]", s):
            return "'" + s.replace("'", "'\\''") + "'"
        return s

    return " ".join(q(a) for a in argv)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Trajectory file path")
    ap.add_argument(
        "--type",
        default=None,
        choices=["dump", "xyz", "bond", "lammpsbondfile", "lammpsdumpfile"],
        help="ReacNetGenerator --type. If omitted, infer from file/header.",
    )
    ap.add_argument("--atomnames", default=None, help="Space-separated atom names for -a, e.g. 'C Cl H O'")
    ap.add_argument("--data", default=None, help="LAMMPS data file for inferring atomnames (optional)")
    ap.add_argument(
        "--pick-data",
        action="store_true",
        help="If multiple data files are found, prompt to choose interactively (TTY only).",
    )

    ap.add_argument("--outroot", default="out", help="Root output directory")
    ap.add_argument("--nohmm", action="store_true", default=True)
    ap.add_argument("--hmm", action="store_true", default=False, help="Enable HMM (overrides --nohmm)")

    ap.add_argument("--stepinterval", type=int, default=10)
    ap.add_argument("--split", type=int, default=1)
    ap.add_argument("--maxspecies", type=int, default=50)
    ap.add_argument("--nproc", type=int, default=None)

    ap.add_argument(
        "--runner",
        choices=["auto", "local", "uvx"],
        default="auto",
        help="How to run: local reacnetgenerator vs uvx fallback",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print planned commands and exit")

    args = ap.parse_args()

    inpath = Path(args.input).expanduser().resolve()
    if not inpath.exists():
        die(f"Input not found: {inpath}")

    rtype = args.type
    if rtype is None:
        rtype = "xyz" if inpath.suffix.lower() == ".xyz" else "dump"

    base = inpath.stem
    outdir = Path(args.outroot).expanduser().resolve() / base
    outdir.mkdir(parents=True, exist_ok=True)

    work_input = inpath

    if rtype == "dump":
        mode = detect_dump_coord_mode(inpath)
        if mode == "scaled":
            converted = outdir / "dump_with_xyz.lammpstrj"
            conv_script = HERE / "convert_lammps_xs_to_x.py"
            conv_argv = ["python3", str(conv_script), "-i", str(inpath), "-o", str(converted)]
            if args.dry_run:
                print("[plan] convert scaled dump -> xyz dump")
                print(argv_to_pretty(conv_argv))
            else:
                run_argv(conv_argv, log_path=outdir / "convert.log", cwd=outdir)
            work_input = converted
        elif mode == "xyz":
            work_input = inpath
        else:
            die(f"Cannot detect coordinates in dump ATOMS header for: {inpath}")

    atomnames_str = args.atomnames
    if not atomnames_str:
        data_file = choose_data_file(inpath, args.data, pick_data=args.pick_data, dry_run=args.dry_run)
        if data_file:
            infer_script = HERE / "infer_atomnames_from_lammps_data.py"
            infer_argv = ["python3", str(infer_script), str(data_file)]
            if args.dry_run:
                print("[plan] infer atomnames from data file:", data_file)
                print(argv_to_pretty(infer_argv))
                atomnames = ["<from", "data>"]
            else:
                atomnames_str = subprocess.check_output(infer_argv, text=True).strip()
                atomnames = atomnames_str.split()
        else:
            die("Missing atomnames. Provide --atomnames 'C H O' or --data path/to/file.data")
    else:
        atomnames = atomnames_str.split()

    if not atomnames or any(" " in a for a in atomnames):
        die(f"Bad atomnames: {atomnames!r}. Provide like: --atomnames 'C Cl H O'")

    local_ok = shutil.which("reacnetgenerator") is not None
    if args.runner == "local" and not local_ok:
        die("runner=local requested but reacnetgenerator not found on PATH")

    if args.runner == "uvx" or (args.runner == "auto" and not local_ok):
        prefix_argv = ["uvx", "--from", "reacnetgenerator", "reacnetgenerator"]
        runner_label = "uvx --from reacnetgenerator reacnetgenerator"
    else:
        prefix_argv = ["reacnetgenerator"]
        runner_label = "reacnetgenerator"

    rng_argv: list[str] = []
    rng_argv += prefix_argv
    rng_argv += ["--type", rtype]
    rng_argv += ["-i", str(work_input)]
    rng_argv += ["-a", *atomnames]

    if not args.hmm:
        rng_argv += ["--nohmm"]
    rng_argv += ["--stepinterval", str(args.stepinterval)]
    rng_argv += ["--split", str(args.split)]
    rng_argv += ["--maxspecies", str(args.maxspecies)]
    if args.nproc:
        rng_argv += ["--nproc", str(args.nproc)]

    if args.dry_run:
        print("[plan] run ReacNetGenerator in:", outdir)
        print(argv_to_pretty(rng_argv))
        return

    run_argv(rng_argv, log_path=outdir / "run.log", cwd=outdir)

    summary = outdir / "summary.md"
    rel_files = sorted([p.relative_to(outdir) for p in outdir.rglob("*") if p.is_file()])
    htmls = sorted(outdir.glob("*.html"))
    report = htmls[0] if htmls else None

    summary.write_text(
        "\n".join(
            [
                "# ReacNetGenerator run summary",
                "",
                f"- input: `{inpath}`",
                f"- type: `{rtype}`",
                f"- atomnames: `{ ' '.join(atomnames) }`",
                f"- stepinterval: `{args.stepinterval}`",
                f"- split: `{args.split}`",
                f"- maxspecies: `{args.maxspecies}`",
                f"- runner: `{runner_label}`",
                f"- workdir: `{outdir}`",
                "",
                "## Report",
                f"- {report.name if report else '(none)'}",
                "",
                "## Output files",
                *[f"- `{p}`" for p in rel_files],
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"OK. Outputs in: {outdir}")
    if report:
        print(f"Report: {report}")


if __name__ == "__main__":
    main()
