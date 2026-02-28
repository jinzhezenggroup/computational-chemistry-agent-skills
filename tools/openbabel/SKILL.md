---
name: openbabel
description: Use Open Babel CLI to convert molecular file formats, generate 3D structures from SMILES, render 2D structure images, and prepare Gaussian input files for computational chemistry workflows.
compatibility: Requires uv and internet access (uses `uvx --from openbabel-wheel obabel ...`).
metadata:
  author: njzjz-bot
  version: "1.1"
  repository: https://github.com/openbabel/openbabel
---

# Open Babel

This skill provides practical Open Babel command patterns for common chemistry data tasks.

## Quick Start

Check installation through uvx:

```bash
uvx --from openbabel-wheel obabel -V
```

Typical conversion syntax:

```bash
uvx --from openbabel-wheel obabel input.ext -i<input_format> -o<output_format> -O output.ext
```

## Core Tasks

### 1) File format conversion

Convert XYZ to PDB:

```bash
uvx --from openbabel-wheel obabel C.xyz -ixyz -opdb -O C.pdb
```

Open Babel supports a large set of chemistry formats (e.g., xyz, mol, mol2, pdb, smi, Gaussian gjf/log/fchk, etc.).

### 2) Build structures from SMILES

Generate methane (3D coordinates required):

```bash
uvx --from openbabel-wheel obabel -:C --gen3d -omol -O C.mol
```

Generate a single carbon atom:

```bash
uvx --from openbabel-wheel obabel -:[C] --gen3d -omol -O C.mol
```

Generate methyl radical:

```bash
uvx --from openbabel-wheel obabel -:[CH3] --gen3d -omol -O CH3.mol
```

> Important: quote SMILES when they contain brackets or special characters.

Equivalent explicit form:

```bash
uvx --from openbabel-wheel obabel -:"[C]([H])([H])[H]" --gen3d -omol -O CH3.mol
```

### 3) Export SMILES from one or more structure files

```bash
uvx --from openbabel-wheel obabel C.mol C.mol2 C.pdb C.xyz --osmi -O C.smi
```

### 4) Render 2D structure images

Generate PNG:

```bash
uvx --from openbabel-wheel obabel -:"C([C@@H](C(=O)O)N)S" -opng -O cys.png
```

Generate SVG:

```bash
uvx --from openbabel-wheel obabel -:"C([C@@H](C(=O)O)N)S" -osvg -O cys.svg
```

Convert Gaussian log directly to image:

```bash
uvx --from openbabel-wheel obabel phosphate.log -ilog -opng -O phosphate.png
```

### 5) Gaussian workflow helper

Generate Gaussian input from SMILES, then patch header with `sed`:

```bash
uvx --from openbabel-wheel obabel -:CC --gen3d -ogjf | sed "1c %nproc=28\n#opt b3lyp/6-31g(d,p)" > CC.gjf
```

Generate next-step input from a previous Gaussian log:

```bash
uvx --from openbabel-wheel obabel CC.log -ilog -ogjf | sed "1c %nproc=28\n#freq b3lyp/6-31g(d,p)" > CC2.gjf
```

## Agent Checklist

When using this skill for users:

1. Confirm source file(s) and desired target format.
2. Prefer explicit `-i` and `-o` format flags for reproducibility.
3. Add `--gen3d` when converting SMILES to coordinate-bearing structures.
4. Quote SMILES strings that contain brackets/parentheses.
5. For Gaussian workflows, verify route section and resource lines (`%nproc`, method/basis) after generation.
6. Use `uvx --from openbabel-wheel obabel ...` consistently to minimize local dependency setup.

## References

- Open Babel project: https://openbabel.org/
- Open Babel GitHub: https://github.com/openbabel/openbabel
- openbabel-wheel package: https://pypi.org/project/openbabel-wheel/
