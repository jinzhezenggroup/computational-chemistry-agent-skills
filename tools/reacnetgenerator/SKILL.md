---
name: reacnetgenerator
description: Run ReacNetGenerator on LAMMPS trajectories to generate reaction networks and reports. Use when the user wants to analyze reactive MD trajectories with ReacNetGenerator (dump/xyz/bond). Handles common LAMMPS dump quirks like x/y/z vs xs/ys/zs scaled coordinates by converting to x/y/z (orthorhombic + triclinic supported via reacnet-md-tools >= 0.1.1), infers atomname order from a LAMMPS data file when available, runs via local reacnetgenerator or via `uvx --from reacnetgenerator`, and writes outputs into out/<input_basename>/ with logs and a summary.
---

## Quick start (agent)

1. Ask for or infer:

- input trajectory path(s)
- input type: dump | xyz | bond (default dump if LAMMPS "ITEM:" is detected)
- atom names order for `-a` (infer from LAMMPS data file if present)

2. Prefer running the pipeline tool from PyPI (do not hand-compose long commands):

- Use `reacnet-md-tools` → `rng-pipeline`.

If multiple `.data` files exist, either pass `--data path/to/file.data` or use `--pick-data` for interactive selection.

## Commands (preferred)

```bash
uvx --refresh --from 'reacnet-md-tools>=0.1.1' rng-pipeline \
    --input /path/to/trajectory.lammpstrj \
    --type dump \
    --outroot out \
    --pick-data \
    --nohmm \
    --stepinterval 10 \
    --maxspecies 50
```

## What this skill does

- Detect whether a LAMMPS dump uses `x y z` or scaled `xs ys zs` coordinates.
- If scaled coords are present:
  - Convert to `x y z` using BOX BOUNDS (orthorhombic + triclinic with tilt factors `xy xz yz`).
  - Requires `reacnet-md-tools >= 0.1.1`.
  - Write the converted dump as `out/<basename>/dump_with_xyz.lammpstrj`.
- Infer `-a/--atomname` order from a LAMMPS data file in the same directory (optional):
  - Parse `Masses` section and map common masses to elements (C, H, O, Cl, N, F, S, P, Br, I, etc.).
  - If inference is ambiguous, stop and ask the user.
- Run ReacNetGenerator:
  - Prefer `reacnetgenerator` if available on PATH.
  - Otherwise run via `uvx --refresh --from reacnetgenerator reacnetgenerator ...`.
- Put all outputs in `out/<basename>/`:
  - `run.log` (stdout/stderr)
  - generated `*.html`, `*.svg`, `*.json`, `*.species`, `*.reaction`, etc.
  - `summary.md` listing key outputs and parameters

## Version check (agent)

```bash
uvx --refresh --from 'reacnet-md-tools>=0.1.1' python -c "import reacnet_md_tools; print(reacnet_md_tools.__version__)"
```

If you still see errors on triclinic dumps:

- ensure your run is resolving `reacnet-md-tools >= 0.1.1` (use `--refresh`), or
- re-dump trajectories with `x y z` instead of `xs ys zs`.

## Default parameters (safe, adjustable)

- `--nohmm` (default ON unless user explicitly wants HMM)
- `--stepinterval 10` for a quick first pass (ask user; default to 1 if they want the full trajectory)
- `--maxspecies 50` (adjustable)
- `--split 1`

## Usage pattern (what to ask the user)

Ask only what you need:

- "What is the trajectory file path? (e.g., .lammpstrj/.xyz/.reaxc)"
- "Which input type should be used: dump/xyz/bond? If unsure, I can auto-detect."
- "Do you have a LAMMPS data file (.data) in the same directory to infer the element order? Otherwise, provide the atomname list (e.g., C Cl H O)."
- "What stride/stepinterval should be used? For a quick sanity run, 10 is fine."

## Notes / limitations

- If your dump already contains `x y z`, no conversion is needed.
