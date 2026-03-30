---
name: rdkit-conf
description: >
  A standardized CLI wrapper for RDKit 3D/2D conformer generation that samples multiple
  conformers per molecule (ETKDGv3, default 10), optimizes each with a force field
  (MMFF94s/UFF), keeps the lowest-energy conformer, automatically falls back to 2D layout
  on total embedding failure with a printed warning, and writes results to SDF or XYZ format.
  USE WHEN you need to generate 3D (or 2D fallback) molecular geometries from SMILES
  datasets (.csv/.smi) for downstream tasks such as docking, visualization, or
  3D-descriptor computation.
compatibility: Requires uv. Dependencies (rdkit, pandas) are declared as PEP 723 inline script metadata and are installed automatically when the script is invoked with `uv run <script_path>` (do NOT use `uv run python <script_path>` -- that bypasses the inline metadata and will not install dependencies automatically).
metadata:
  author: luzitian
  version: '1.0'
  repository: https://github.com/rdkit/rdkit
---

# RDKit Conformer Generation

This skill provides practical command patterns for **RDKit 3D/2D conformer generation**
using the standardized CLI wrapper: `<skill_path>/scripts/rdkit_conf_helper.py`.

Key behaviors (important for Agents):

- The script prints **environment detection** (Python/RDKit/Pandas) by default.
- **Multi-conformer sampling**: embeds `--num-confs` conformers (default 10) per molecule
  via `EmbedMultipleConfs`, optimizes each with the chosen force field, and keeps the
  **lowest-energy** one. Set `--num-confs 1` to revert to single-conformer behavior.
- **2D fallback**: if all 3D embedding attempts fail, `Compute2DCoords` is used instead
  and a `[WARN]` line is printed to stderr for that molecule.
- Bad/illegal SMILES are **skipped entirely** and logged to `*.skipped.csv` (no crash).
- Molecules that fell back to 2D are **additionally logged** to `*.fallback.csv`.
- Each run ends with a summary line and **absolute output paths**:
  - `[INFO] Done: <N_3d> 3D, <N_2d> 2D-fallback, <N_skip> skipped (total input: <N>)`
  - `[RESULT] conf_sdf=/abs/path.sdf`
  - `[RESULT] conf_xyz=/abs/path.xyz`
  - `[RESULT] fallback_csv=/abs/path.fallback.csv` (only if any 2D fallbacks occurred)
  - `[RESULT] skipped_csv=/abs/path.skipped.csv` (only if any SMILES were skipped)

## Quick Start

Check CLI help:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py --help
uv run <skill_path>/scripts/rdkit_conf_helper.py conf --help
```

Disable environment printing (optional):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py --no-env conf --smiles "CCO" --output out.sdf
```

## Core Tasks

### 1) Generate 3D conformers (SDF output, default)

Single SMILES:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --smiles "CCO" \
    --output /tmp/CCO.sdf
```

Single SMILES with a custom molecule name:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --smiles "c1ccccc1" \
    --name benzene \
    --output /tmp/benzene.sdf
```

From CSV (default SMILES column: `smiles`):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv \
    --smiles-col smiles \
    --output data.sdf
```

From CSV with a name column:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv \
    --smiles-col smiles \
    --name-col compound_id \
    --output data.sdf
```

From SMI (second token per line is used as name automatically):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file molecules.smi \
    --output molecules.sdf
```

### 2) Control conformer sampling count

Default (10 conformers sampled, lowest-energy kept):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --output data.sdf
```

Single conformer (fastest, least thorough):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --num-confs 1 --output data.sdf
```

Increase sampling for flexible or macrocyclic molecules:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --num-confs 50 --output data.sdf
```

### 3) Choose force-field minimization

MMFF94s (default, falls back to UFF if unavailable):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --ff mmff94s --output data.mmff.sdf
```

UFF (universal force field):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --ff uff --output data.uff.sdf
```

Skip force-field optimization (raw ETKDG geometry only):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --ff none --output data.etkdg_raw.sdf
```

### 4) XYZ output

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv \
    --format xyz \
    --output data.xyz
```

### 5) Tuning embedding for difficult molecules

Large or macrocyclic molecules sometimes fail standard ETKDG; try random initial coordinates:

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file macrocycles.csv \
    --use-random-coords \
    --max-attempts 500 \
    --output macrocycles.sdf
```

Use a different random seed (reproducibility):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --seed 123 --output data.seed123.sdf
```

Non-deterministic embedding (seed = -1):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --seed -1 --output data.sdf
```

### 6) Suppress hydrogen addition

By default explicit H atoms are added before embedding for more accurate 3D geometry.
Use `--no-hs` to keep the molecule as-is (heavy atoms only):

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv --no-hs --output data.noh.sdf
```

### 7) Custom log file paths

```bash
uv run <skill_path>/scripts/rdkit_conf_helper.py conf \
    --file data.csv \
    --output data.sdf \
    --error-log logs/skipped.csv \
    --fallback-log logs/used_2d.csv
```

______________________________________________________________________

## 3D Embedding Pipeline Details

For each molecule, the script runs the following steps in order:

1. **Parse SMILES** via `Chem.MolFromSmiles`.
1. **Add hydrogens** (`Chem.AddHs`) -- skipped with `--no-hs`.
1. **Multi-conformer 3D embedding** (`EmbedMultipleConfs`, `--num-confs` candidates,
   default 10): tries ETKDGv3, then ETKDGv2, then ETDG, then ETDG+`useRandomCoords`
   as a fallback chain until at least one conformer is embedded.
1. **Force-field minimization** (if `--ff` is not `none`): each successfully embedded
   conformer is individually optimized. MMFF94s transparently falls back to UFF if
   parameters are unavailable for that molecule.
1. **Lowest-energy selection**: the conformer with the minimum post-optimization energy
   is retained; all others are discarded. If `--ff none`, the first embedded conformer
   is kept without energy ranking.
1. **2D fallback** (if all 3D attempts yield zero conformers): generates a flat 2D layout
   via `Compute2DCoords` (Z=0 for all atoms), prints a `[WARN]` to stderr, and records
   the molecule in the fallback log.

______________________________________________________________________

## Output Format Notes

**SDF output (`--format sdf`, default):**

- Standard V2000 multi-molecule SDF, one conformer per molecule.
- Molecule name (from `--name`, `--name-col`, or auto-generated `mol_<i>`) is
  written to the SDF header line.
- Compatible with most cheminformatics tools (RDKit, OpenBabel, Schrodinger, etc.).

**XYZ output (`--format xyz`):**

- Concatenated XYZ blocks (element, x, y, z per atom).
- Molecule name is written as the comment line (second line of each block).
- Coordinates are in Angstroms.
- Note: if `--no-hs` is used, hydrogen atoms are absent from the XYZ.

**Fallback log (`*.fallback.csv`):**

- Written only when at least one molecule fell back to 2D.
- Columns: `idx`, `smiles`, `name`, `dim` (always 2), `ff` (always `2d_fallback`), `note`.

**Skipped log (`*.skipped.csv`):**

- Written only when at least one SMILES was skipped.
- Columns: `idx`, `smiles`, `error`.

______________________________________________________________________

## Agent Checklist

When using this skill for users:

1. Confirm input format:
   - `.csv` requires a SMILES column (default `smiles`)
   - `.smi` uses the first token per line as SMILES, second token (if present) as name
1. Quote SMILES containing special shell characters (brackets/parentheses):
   - Example: `--smiles "[C@@H](O)(F)Cl"`
1. For CSV workflows, verify column names:
   - `--smiles-col` for the SMILES column
   - `--name-col` (optional) for molecule identifiers to embed in SDF/XYZ headers
1. Check the `[INFO] Done:` summary line for the 3D/2D/skip breakdown.
1. If 2D fallbacks occurred, inspect `*.fallback.csv`:
   - Consider `--use-random-coords` or `--max-attempts` tuning for the affected SMILES.
   - 2D conformers have Z=0 and are not suitable for 3D-based applications (docking, 3D QSAR).
1. Always capture absolute output paths:
   - Look for `[RESULT] ...=/abs/path` in stdout.
1. If debugging is needed, enable full traceback:
   - `RDKIT_CONF_HELPER_TRACE=1 uv run <skill_path>/scripts/rdkit_conf_helper.py ...`

## References

- RDKit conformer generation guide: https://www.rdkit.org/docs/GettingStartedInPython.html#working-with-3d-molecules
- ETKDG paper: Riniker & Landrum, J. Chem. Inf. Model. 2015, 55, 2562
- ETKDGv3: Wang et al., J. Chem. Inf. Model. 2020, 60, 2044
