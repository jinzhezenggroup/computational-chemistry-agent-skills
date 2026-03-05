---
name: unimol
description: A robust, end-to-end CLI wrapper for Uni-Mol that standardizes molecular ML workflows. It enables one-line execution for representation extraction, model training, and property prediction, featuring built-in SMILES validation via RDKit for high-throughput reliability.
compatibility: Requires uv. Dependencies (unimol-tools, rdkit, etc.) are handled automatically via inline script metadata in unimol_helper.py.
metadata:
  author: luzitian
  version: "1.0"
  repository: https://github.com/deepmodeling/Uni-Mol
---

# Uni-Mol

This skill provides practical command patterns for **Uni-Mol molecular representation / training / prediction** using the standardized CLI wrapper: `<skill_path>/scripts/unimol_helper.py`.

Key behaviors (important for Agents):

- The script prints **environment detection** (Python/Torch/CUDA) by default.
- Bad/illegal SMILES are **skipped and logged** to `*.skipped.csv` (no crash).
- Each run ends by printing **absolute output paths** like:
  - `[RESULT] repr_npy=/abs/path.npy`
  - `[RESULT] model_dir=/abs/model_dir`
  - `[RESULT] pred_csv=/abs/pred.csv`

## Quick Start

Check CLI help:

```bash
uv run python <skill_path>/scripts/unimol_helper.py --help
```

Check subcommand help:

```bash
uv run python <skill_path>/scripts/unimol_helper.py repr --help
uv run python <skill_path>/scripts/unimol_helper.py train --help
uv run python <skill_path>/scripts/unimol_helper.py predict --help
```

Disable environment printing (optional):

```bash
uv run python <skill_path>/scripts/unimol_helper.py --no-env repr --smiles "CCO" --output out.npy
```

## Core Tasks

### 1) Extract molecular representations (embedding) to .npy

Single SMILES:

```bash
uv run python <skill_path>/scripts/unimol_helper.py repr \
  --smiles "CCO" \
  --output /tmp/ccO.repr.npy
```

From CSV (default SMILES column is `smiles`):

```bash
uv run python <skill_path>/scripts/unimol_helper.py repr \
  --file data.csv \
  --smiles-col smiles \
  --output data.repr.npy
```

From SMI:

```bash
uv run python <skill_path>/scripts/unimol_helper.py repr \
  --file molecules.smi \
  --output molecules.repr.npy
```

Force CPU / GPU:

```bash
# Force CPU
uv run python <skill_path>/scripts/unimol_helper.py repr --smiles "CCO" --no-gpu --output out.npy

# Force GPU (will warn & fall back if CUDA is unavailable)
uv run python <skill_path>/scripts/unimol_helper.py repr --smiles "CCO" --use-gpu --output out.npy
```

### 2) Train a property model (classification / regression)

Regression training (CSV must contain `smiles` and `target` columns):

```bash
uv run python <skill_path>/scripts/unimol_helper.py train \
  --task regression \
  --input train.csv \
  --smiles-col smiles \
  --target-col target \
  --epochs 50 \
  --output ./model_reg
```

Classification training:

```bash
uv run python <skill_path>/scripts/unimol_helper.py train \
  --task classification \
  --input train.csv \
  --smiles-col smiles \
  --target-col target \
  --epochs 50 \
  --output ./model_cls
```

Force CPU:

```bash
uv run python <skill_path>/scripts/unimol_helper.py train \
  --task regression \
  --input train.csv \
  --epochs 50 \
  --output ./model_cpu \
  --no-cuda
```

### 3) Predict properties to .csv

Predict from CSV:

```bash
uv run python <skill_path>/scripts/unimol_helper.py predict \
  --model ./model_reg \
  --input test.csv \
  --smiles-col smiles \
  --output pred.csv
```

Predict from SMI:

```bash
uv run python <skill_path>/scripts/unimol_helper.py predict \
  --model ./model_reg \
  --input test.smi \
  --output pred.csv
```

Notes:

- Output CSV contains the input rows (for valid SMILES) plus `pred` / `pred_*` columns.
- If there are bad SMILES, they are skipped and saved to `pred.csv.skipped.csv` (or your `--error-log` path).

## Agent Checklist

When using this skill for users:

1. Confirm input format:
   - `.csv` requires a SMILES column (default `smiles`)
   - `.smi` uses the first token of each line as SMILES
2. Quote SMILES containing special characters (brackets/parentheses):
   - Example: `--smiles "[C]([H])([H])[H]"`
3. For CSV workflows, verify column names:
   - `repr`: `--smiles-col`
   - `train`: `--smiles-col` and `--target-col`
   - `predict`: `--smiles-col`
4. Watch for skipped SMILES:
   - Check `*.skipped.csv` and decide whether to fix or permanently drop them
5. Always capture absolute output paths:
   - Look for `[RESULT] ...=/abs/path` in stdout
6. If debugging is needed, enable full traceback:
   - `UNIMOL_HELPER_TRACE=1 uv run python <skill_path>/scripts/unimol_helper.py ...`

## References

- Uni-Mol project: https://github.com/fanxiaoyu0/Uni-Mol
- RDKit: https://www.rdkit.org/

