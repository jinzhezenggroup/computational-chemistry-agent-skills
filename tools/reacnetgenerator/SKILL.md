---
name: reacnetgenerator
description: Run ReacNetGenerator on LAMMPS trajectories to generate reaction networks and reports. Use when the user wants to analyze reactive MD trajectories with ReacNetGenerator (dump/xyz/bond). Handles common LAMMPS dump quirks like xs/ys/zs scaled coordinates (orthorhombic boxes only) by converting to x/y/z, infers atomname order from a LAMMPS data file when available, runs via local reacnetgenerator or via `uvx --from reacnetgenerator`, and writes outputs into out/<input_basename>/ with logs and a summary.
---

## Quick start (agent)

1) Ask for or infer:
- input trajectory path(s)
- input type: dump | xyz | bond (default dump if LAMMPS "ITEM:" is detected)
- atom names order for `-a` (infer from LAMMPS data file if present)

2) Prefer running the pipeline script (do not hand-compose long commands):
- Use `scripts/rng_pipeline.py`.

If multiple `.data` files exist, either pass `--data path/to/file.data` or use `--pick-data` for interactive selection.

## What this skill does

- Detect whether a LAMMPS dump uses `x y z` or scaled `xs ys zs` coordinates.
- If scaled coords are present:
  - Convert to `x y z` using BOX BOUNDS for **orthorhombic** boxes.
  - Write the converted dump as `out/<basename>/dump_with_xyz.lammpstrj`.
- Infer `-a/--atomname` order from a LAMMPS data file in the same directory (optional):
  - Parse `Masses` section and map common masses to elements (C, H, O, Cl, N, F, S, P, Br, I, etc.).
  - If inference is ambiguous, stop and ask the user.
- Run ReacNetGenerator:
  - Prefer `reacnetgenerator` if available on PATH.
  - Otherwise run via `uvx --from reacnetgenerator reacnetgenerator ...`.
- Put all outputs in `out/<basename>/`:
  - `run.log` (stdout/stderr)
  - generated `*.html`, `*.svg`, `*.json`, `*.species`, `*.reaction`, etc.
  - `summary.md` listing key outputs and parameters

## Default parameters (safe, adjustable)

- `--nohmm` (default ON unless user explicitly wants HMM)
- `--stepinterval 10` for quick first pass (ask user; default to 1 if they want full trajectory)
- `--maxspecies 50` (adjustable)
- `--split 1`

## Usage pattern (what to ask the user)

Ask only what you need:

- "轨迹文件路径是什么？（例如 .lammpstrj/.xyz/.reaxc）"
- "输入类型用 dump/xyz/bond 哪个？不确定我可以自动识别。"
- "是否有同目录的 LAMMPS data 文件（.data）用来推断元素顺序？否则你给我 atomname 列表（例如 C Cl H O）。"
- "抽帧 stride/stepinterval 多少？先快速跑通可用 10。"

## Commands (for reference)

Prefer the pipeline wrapper:

```bash
python3 scripts/rng_pipeline.py \
  --input /path/to/trajectory.lammpstrj \
  --type dump \
  --outroot out \
  --pick-data \
  --nohmm \
  --stepinterval 10 \
  --maxspecies 50
```

## Notes / limitations

- Only supports orthorhombic boxes for xs->x conversion.
- If the dump is triclinic (xy xz yz), stop and ask for a re-dumped trajectory with x/y/z or implement triclinic conversion.
