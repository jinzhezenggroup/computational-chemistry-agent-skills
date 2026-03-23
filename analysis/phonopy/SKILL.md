---
name: phonopy
description: >
  General phonon-workflow skill built around phonopy, independent of force backend.
  USE WHEN you need to prepare finite-displacement phonon calculations, build force constants,
  and analyze phonon properties (band structure, DOS, thermal quantities) while obtaining
  forces from different engines such as VASP, Quantum ESPRESSO, or ML force fields.
compatibility: Requires phonopy and a force provider workflow (e.g., VASP/QE/MLFF) that can return forces for displaced supercells.
license: BSD-3-Clause
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/phonopy/phonopy
---

# Phonopy (Backend-Agnostic)

Use this skill as a **general phonon orchestration layer**.

It treats force calculation as a pluggable backend step and focuses on `phonopy` data flow.

## Scope

This skill should:

- generate displacement supercells from a user-provided structure
- define and validate force-collection requirements
- build force constants from collected forces
- run phonon analysis (band, DOS, thermal properties)
- summarize assumptions and remaining decisions

This skill should **not**:

- assume a single force engine
- fabricate force data
- submit cluster jobs directly

If execution/submission is required, hand off run steps to submission skills (for example `dpdisp-submit`) and backend-specific input skills.

## Hard requirement

Phonon workflows require both:

- a valid initial structure (unit cell / primitive context)
- force data on displaced supercells (or precomputed force constants)

If either is missing, stop and ask for it.

## Backend abstraction

Force provider may be one of:

- DFT backend (for example VASP or QE)
- ML force field backend (for example DeePMD/LAMMPS)

The role split should be:

1. `phonopy` skill: displacement generation, dataset/force-constant assembly, phonon analysis
1. backend skill: compute forces for each displaced supercell

## Expected workflow

1. Read and validate initial structure.
1. Confirm phonon objective (`band`, `dos`, `thermal`, combinations).
1. Choose supercell and displacement settings.
1. Generate displaced supercells (`phonopy -d` style).
1. Route displaced structures to selected backend for force evaluation.
1. Collect forces and build `FORCE_SETS` or force constants.
1. Run requested phonon analysis and export outputs.
1. Report assumptions, convergence caveats, and next steps.

For concrete command patterns, see `references/commands-and-workflow.md`.

## Parameters to collect

### Must provide

- initial structure file (placeholder examples like `structure.ext` mean real files such
  as `POSCAR`, `.cif`, or other backend-compatible structure formats)
- backend choice for force evaluation
- supercell setting (matrix or size)
- displacement amplitude (`--amplitude` policy)
- target phonon outputs (`band`, `dos`, `thermal`)

### Usually should be explicit

- primitive matrix choice
- symmetry tolerance settings
- q-point mesh for DOS/thermal calculations
- band path definition source (if band requested)

### Task-specific

For `band`:

- high-symmetry path definition
- number of points per segment

For `dos`/`thermal`:

- mesh density
- temperature range/step for thermal properties

## Required behavior

1. Validate structure periodicity and cell.
1. Make backend boundary explicit before running force steps.
1. Keep traceable mapping between each displacement and force file.
1. Check force dataset completeness before force-constant build.
1. Report non-analytic corrections / long-range settings status when relevant.
1. Flag unresolved scientific choices instead of guessing silently.

## Defaulting policy

Allowed only for low-risk defaults with explicit labels.

Reasonable defaults:

- finite-displacement workflow as baseline
- moderate displacement amplitude for first pass
- standard mesh/band resolution for exploratory analysis

Do **not** silently invent:

- backend force results
- production-level convergence settings
- band path conventions when crystal standard is unclear

## Expected output

Provide:

1. generated displacement task layout
1. force-data assembly status (`FORCE_SETS`/force constants)
1. requested phonon outputs (band/DOS/thermal files)
1. explicit assumptions and unresolved decisions
1. handoff guidance if backend execution/submission is pending

## Common failure points

- missing or inconsistent force files for displacements
- supercell too small for stable phonon results
- inconsistent units/conventions across backend outputs
- imaginary modes caused by insufficient convergence or setup choices
- unclear band path convention for non-standard cells
