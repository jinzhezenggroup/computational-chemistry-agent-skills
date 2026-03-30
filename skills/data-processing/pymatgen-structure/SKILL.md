---
name: pymatgen-structure
description: >
  Structure manipulation and crystal analysis workflows based on pymatgen.
  USE WHEN you need to read/write common atomistic formats (CIF, POSCAR, XYZ),
  build supercells, perform site substitution/doping, inspect symmetry
  (space group), or compute local structure descriptors for materials tasks.
compatibility: Requires Python 3.10+ and pymatgen (recommended via uv).
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/materialsproject/pymatgen
---

# pymatgen Structure Operations

Use this skill to perform **structure preprocessing and analysis** with `pymatgen`.

## Scope

This skill should:

- require at least one user-provided structure file
- parse and normalize common structure formats
- perform requested geometry edits (for example supercell, substitution)
- run basic crystal analysis (for example symmetry, composition)
- write explicit output files and summarize key changes

This skill should **not**:

- submit HPC jobs
- run expensive DFT/MD production calculations
- invent missing scientific intent (for example random doping strategy) without confirmation

If the user asks for DFT submission, hand off to a submission skill such as `dpdisp-submit` after preprocessing is done.

## Hard requirement

The user must provide an input structure source (file path or explicit coordinates + lattice).

If structure input is missing, stop and ask for it.

## Supported input/output formats

Typical input formats:

- `cif`
- `POSCAR` / `CONTCAR`
- `xyz` (for non-periodic or when cell is provided separately)
- other formats supported by `pymatgen` IO backends

Typical output formats:

- `cif`
- `POSCAR`
- `xyz`
- optional JSON summaries

## Expected workflow

1. Read user-provided structure.
1. Validate periodicity and cell information.
1. Confirm requested operation (convert, supercell, substitution, analysis).
1. Collect only missing critical parameters.
1. Execute operation via `pymatgen`.
1. Write output structure(s) and a short result summary.
1. If requested, prepare handoff-ready files for downstream skills.

For concrete command patterns, see `references/commands-and-workflow.md`.

## Operations this skill should handle

### A) Format conversion

- convert between `cif` / `POSCAR` / `xyz`
- preserve lattice and species ordering when possible

### B) Supercell construction

- apply scaling matrix, for example `[[2,0,0],[0,2,0],[0,0,1]]`
- report final atom count and new lattice vectors

### C) Substitution / doping-like edits

- deterministic site substitution by species or by explicit site index
- report stoichiometry before/after
- ask user before applying random substitutions

### D) Symmetry and composition analysis

- reduced formula
- lattice parameters
- space group symbol/number
- optional primitive/conventional standardization when explicitly requested

### E) Local environment quick checks

- nearest-neighbor distances or coordination-style summaries
- report method/threshold assumptions

## Parameters to collect

### Must provide

- input structure path
- target operation type
- output path (or output naming rule)

### Operation-specific

For format conversion:

- output format

For supercell:

- scaling matrix or `(na, nb, nc)`

For substitution:

- source species/site selection
- target species
- substitution fraction or exact indices

For symmetry analysis:

- symmetry tolerance (if non-default behavior is desired)

## Required behavior

1. Check file existence/readability before processing.
1. Detect and report missing lattice info for periodic workflows.
1. Do not silently drop atoms or reorder species without notice.
1. Explicitly show assumptions (for example tolerance values).
1. Return exact output file paths.

## Defaulting policy

Allowed only for low-risk defaults, clearly labeled.

Reasonable defaults:

- symmetry tolerance defaults from `pymatgen` when user does not specify
- output basename derived from input name + operation suffix

Do **not** silently invent:

- lattice for periodic systems
- substitution ratio for doping tasks
- magnetic/electronic settings (outside this skill's scope)

## Expected output

Provide:

1. output file path(s)
1. concise summary of changes (atom count, composition, lattice deltas)
1. analysis result highlights (for example space group)
1. explicit assumptions and unresolved choices
1. next-step suggestion when user wants downstream DFT/MD submission

## Common failure points

- unreadable input file or ambiguous format
- xyz input lacking periodic cell when periodic workflow is requested
- invalid scaling matrix or impossible substitution request
- too aggressive tolerances causing unstable symmetry classification
