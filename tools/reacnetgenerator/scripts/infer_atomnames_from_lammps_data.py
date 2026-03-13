#!/usr/bin/env python3
"""Infer `reacnetgenerator -a` atomname order from a LAMMPS data file.

Reads the `Masses` section and maps masses to element symbols using a nearest-match heuristic.
Stops if any type is ambiguous.

This is meant as a convenience; users should confirm the mapping.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# Common elements in reactive MD datasets
MASS_TO_EL = {
    "H": 1.00794,
    "C": 12.0107,
    "N": 14.0067,
    "O": 15.9994,
    "F": 18.9984,
    "P": 30.9738,
    "S": 32.065,
    "Cl": 35.453,
    "Br": 79.904,
    "I": 126.904,
}

# Acceptable relative error for a match
REL_TOL = 0.01  # 1%


def parse_masses(data_text: str) -> dict[int, float]:
    # Find Masses section
    m = re.search(r"^Masses\s*$", data_text, flags=re.MULTILINE)
    if not m:
        raise ValueError("No 'Masses' section found")

    lines = data_text[m.end():].splitlines()
    masses: dict[int, float] = {}
    for ln in lines:
        s = ln.strip()
        if not s:
            # blank line ends section in typical LAMMPS data, but some files have blanks inside
            continue
        # Stop when the next section begins
        if re.match(r"^(Atoms|Velocities|Bonds|Angles|Dihedrals|Impropers)\b", s):
            break
        # Parse: type mass [comment]
        parts = s.split()
        if len(parts) < 2:
            continue
        try:
            t = int(parts[0])
            mass = float(parts[1])
        except Exception:
            continue
        masses[t] = mass

    if not masses:
        raise ValueError("No masses parsed from Masses section")
    return masses


def match_element(mass: float) -> str:
    candidates = []
    for el, ref in MASS_TO_EL.items():
        rel = abs(mass - ref) / ref
        if rel <= REL_TOL:
            candidates.append((rel, el, ref))
    candidates.sort()
    if not candidates:
        raise ValueError(f"No element match for mass={mass}")

    # If two are very close (unlikely with this set), treat as ambiguous
    if len(candidates) >= 2 and (candidates[1][0] - candidates[0][0]) < 1e-6:
        raise ValueError(f"Ambiguous mass match for mass={mass}: {candidates[:2]}")

    return candidates[0][1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="LAMMPS data file path")
    args = ap.parse_args()

    text = Path(args.data).read_text(encoding="utf-8", errors="replace")
    masses = parse_masses(text)

    max_type = max(masses)
    atomnames = []
    for t in range(1, max_type + 1):
        if t not in masses:
            raise SystemExit(f"ERROR: Missing mass for atom type {t} in {args.data}")
        atomnames.append(match_element(masses[t]))

    print(" ".join(atomnames))


if __name__ == "__main__":
    main()
