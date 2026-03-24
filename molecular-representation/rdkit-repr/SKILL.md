---
name: rdkit-repr
description: >
  A standardized CLI wrapper for RDKit molecular featurization workflows that handles
  physicochemical descriptor computation (outputs .csv) and molecular fingerprint extraction
  (outputs .npy or .csv), with built-in SMILES validation.
  USE WHEN you need to compute RDKit molecular descriptors or fingerprints from SMILES
  datasets (.csv/.smi), or when you want to list all available descriptor names and presets.
compatibility: Requires uv. Dependencies (rdkit, pandas, numpy) are declared as PEP 723 inline script metadata and are installed automatically when the script is invoked with `uv run <script_path>` (do NOT use `uv run python <script_path>` -- that bypasses the inline metadata and will not install dependencies automatically).
metadata:
  author: luzitian
  version: '1.0'
  repository: https://github.com/rdkit/rdkit
---

# RDKit Molecular Featurization

This skill provides practical command patterns for **RDKit descriptor and fingerprint extraction**
using the standardized CLI wrapper: `<skill_path>/scripts/rdkit_helper.py`.

Key behaviors (important for Agents):

- The script prints **environment detection** (Python/RDKit/NumPy/Pandas) by default.
- Bad/illegal SMILES are **skipped and logged** to `*.skipped.csv` (no crash).
- Each run ends by printing **absolute output paths** like:
  - `[RESULT] desc_csv=/abs/path.csv`
  - `[RESULT] fp_npy=/abs/path.npy`
  - `[RESULT] fp_csv=/abs/path.csv`

## Quick Start

Check CLI help:

```bash
uv run <skill_path>/scripts/rdkit_helper.py --help
```

Check subcommand help:

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc --help
uv run <skill_path>/scripts/rdkit_helper.py fp --help
uv run <skill_path>/scripts/rdkit_helper.py list-desc --help
```

Disable environment printing (optional):

```bash
uv run <skill_path>/scripts/rdkit_helper.py --no-env desc --smiles "CCO" --output out.csv
```

## Core Tasks

### 1) Compute physicochemical descriptors → .csv

Single SMILES (default preset: `physchem`, 25 descriptors):

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --smiles "CCO" \
    --output /tmp/CCO.desc.csv
```

From CSV (default SMILES column is `smiles`):

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv \
    --smiles-col smiles \
    --output data.desc.csv
```

From SMI:

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file molecules.smi \
    --output molecules.desc.csv
```

Choose a descriptor preset:

```bash
# Lipinski drug-likeness (6 descriptors: MolWt, MolLogP, NumHDonors, ...)
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv --preset lipinski --output data.lipinski.csv

# Extended physicochemical (25 descriptors, default)
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv --preset physchem --output data.physchem.csv

# Topological / graph indices (56 descriptors: BalabanJ, BertzCT, Chi*, PEOE_VSA*, ...)
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv --preset topological --output data.topo.csv

# All RDKit descriptors (~200 descriptors)
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv --preset all --output data.all_desc.csv
```

Select specific descriptors (overrides `--preset`):

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv \
    --descriptors "MolWt,MolLogP,TPSA,NumHDonors,NumHAcceptors" \
    --output data.custom.csv
```

Suppress merging back original CSV columns (output only smiles + descriptors):

```bash
uv run <skill_path>/scripts/rdkit_helper.py desc \
    --file data.csv --preset physchem --no-merge --output data.desc_only.csv
```

______________________________________________________________________

### 2) Compute molecular fingerprints → .npy or .csv

Available fingerprint types:

| Type            | Description                                                | Default bits |
| --------------- | ---------------------------------------------------------- | ------------ |
| `morgan2`       | Morgan circular FP radius 2 (ECFP4-like), bit vector       | 2048         |
| `morgan3`       | Morgan circular FP radius 3 (ECFP6-like), bit vector       | 2048         |
| `morgan2_count` | Morgan radius-2 count vector                               | 2048         |
| `rdkit`         | RDKit path-based FP, bit vector                            | 2048         |
| `maccs`         | MACCS 167 structural keys (bit vector, `--nbits` ignored)  | 167          |
| `topological`   | Topological torsion FP (count vector, hashed to `--nbits`) | 2048         |
| `atompair`      | Atom-pair FP (count vector, hashed to `--nbits`)           | 2048         |
| `layered`       | Layered substructure FP, bit vector                        | 2048         |
| `pattern`       | SMARTS pattern FP, bit vector                              | 2048         |

Single SMILES, output as NumPy array (.npy):

```bash
uv run <skill_path>/scripts/rdkit_helper.py fp \
    --smiles "CCO" \
    --type morgan2 \
    --output /tmp/CCO.morgan2.npy
```

From CSV, Morgan ECFP4 (2048 bits):

```bash
uv run <skill_path>/scripts/rdkit_helper.py fp \
    --file data.csv \
    --smiles-col smiles \
    --type morgan2 \
    --nbits 2048 \
    --output data.morgan2.npy
```

From SMI, MACCS keys (always 167 bits):

```bash
uv run <skill_path>/scripts/rdkit_helper.py fp \
    --file molecules.smi \
    --type maccs \
    --output molecules.maccs.npy
```

Output as CSV (smiles + bit_0 … bit_N-1 columns):

```bash
uv run <skill_path>/scripts/rdkit_helper.py fp \
    --file data.csv \
    --type rdkit \
    --nbits 1024 \
    --format csv \
    --output data.rdkfp.csv
```

Atom-pair fingerprint, 4096 bits:

```bash
uv run <skill_path>/scripts/rdkit_helper.py fp \
    --file data.csv \
    --type atompair \
    --nbits 4096 \
    --output data.atompair.npy
```

______________________________________________________________________

### 3) List available descriptors

List all descriptors and built-in presets:

```bash
uv run <skill_path>/scripts/rdkit_helper.py list-desc
```

List descriptors in a specific preset group:

```bash
uv run <skill_path>/scripts/rdkit_helper.py list-desc --group lipinski
uv run <skill_path>/scripts/rdkit_helper.py list-desc --group physchem
uv run <skill_path>/scripts/rdkit_helper.py list-desc --group topological
uv run <skill_path>/scripts/rdkit_helper.py list-desc --group all
```

______________________________________________________________________

## Descriptor Presets Reference

| Preset        | Count | Typical Use                                                            |
| ------------- | ----- | ---------------------------------------------------------------------- |
| `lipinski`    | 6     | Quick drug-likeness screening (Ro5 filter)                             |
| `physchem`    | 25    | General ML features: MW, logP, TPSA, ring counts, charge stats, …      |
| `topological` | 56    | Graph/topology indices: Balaban J, Kappa, Chi, PEOE_VSA, EState_VSA, … |
| `all`         | ~200  | Full RDKit descriptor set (includes fragment counts, MQN, etc.)        |

______________________________________________________________________

## Output Format Notes

**`desc` output (CSV):**

- Columns: `smiles`, then one column per descriptor.
- When `--file` is a `.csv` and `--no-merge` is not set, original CSV columns are appended.
- Rows only contain valid SMILES (invalid ones are logged to `*.skipped.csv`).

**`fp` output:**

- `.npy` (default): NumPy array of shape `(N_valid, nbits)`, dtype `uint8` (bit) or `int32` (count).
- `.csv`: `smiles` column followed by `bit_0` … `bit_{nbits-1}` columns.
- MACCS keys always produce 167 bits regardless of `--nbits`.

______________________________________________________________________

## Agent Checklist

When using this skill for users:

1. Confirm input format:
   - `.csv` requires a SMILES column (default `smiles`)
   - `.smi` uses the first token of each line as SMILES
1. Quote SMILES containing special shell characters (brackets/parentheses):
   - Example: `--smiles "[C@@H](O)(F)Cl"`
1. For CSV workflows, verify column names:
   - `desc`: `--smiles-col`
   - `fp`: `--smiles-col`
1. Choose the right preset or fingerprint type for the downstream task:
   - Drug screening / Ro5: `--preset lipinski`
   - General ML featurization: `--preset physchem` or `--type morgan2`
   - Structural similarity search: `--type morgan2` or `--type rdkit`
   - Substructure matching: `--type maccs` or `--type pattern`
1. Watch for skipped SMILES:
   - Check `*.skipped.csv` and decide whether to fix or permanently drop them
1. Always capture absolute output paths:
   - Look for `[RESULT] ...=/abs/path` in stdout
1. If debugging is needed, enable full traceback:
   - `RDKIT_HELPER_TRACE=1 uv run <skill_path>/scripts/rdkit_helper.py ...`

## References

- RDKit documentation: https://www.rdkit.org/docs/
- RDKit descriptor list: https://www.rdkit.org/docs/GettingStartedInPython.html#list-of-available-descriptors
- RDKit fingerprint guide: https://www.rdkit.org/docs/GettingStartedInPython.html#fingerprinting-and-molecular-similarity
