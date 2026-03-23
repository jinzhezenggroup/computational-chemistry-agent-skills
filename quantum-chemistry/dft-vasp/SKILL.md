---
name: dft-vasp
description: Generate VASP DFT input tasks from a user-provided structure plus user-specified DFT settings. Use when the user wants to prepare VASP calculations for static SCF and structural relaxation workflows, including robust INCAR generation with KSPACING-based k-point policy (KPOINTS optional) and explicit POTCAR mapping. This skill prepares VASP input tasks only; use a separate submission skill such as dpdisp-submit for execution.
compatibility: Requires a user-provided initial structure and valid VASP pseudopotential resources/license in the target environment.
license: MIT
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://vasp.at/
---

# DFT with VASP

Use this skill to **build VASP DFT tasks** from a user-provided structure and DFT settings.

## Scope

This skill should:

- require a user-provided structure
- read or normalize structure input into VASP-ready form
- identify the target calculation type (`static`, `relax`)
- collect only missing critical DFT settings
- generate VASP input files (`POSCAR`, `INCAR`, optional `KPOINTS`)
- provide explicit POTCAR mapping/assembly instructions
- organize a handoff-ready task directory
- state assumptions and unresolved choices

This skill should **not**:

- submit jobs
- manage schedulers
- handle remote execution
- fabricate unavailable pseudopotential files

If submission is requested, hand off to `dpdisp-submit` after input generation.

## Hard requirement

The user must provide a structure.

Do not generate a VASP task without a user-provided structure source. If missing, stop and ask for it.

## Supported task types (v0.1)

- `static` (single-point SCF)
- `relax` (geometry relaxation)

`dos` / `band` are intentionally out of scope for this version.

## Structure input convention

Accept common structure sources such as `POSCAR`, `CONTCAR`, `cif`, `xyz` (with cell information for periodic systems).

If conversion is needed, use `dpdata-cli` or `pymatgen-structure` first.

For periodic systems, ensure lattice/cell is preserved and consistent.

## Expected workflow

1. Start from a user-provided structure.
1. Normalize structure to `POSCAR` if needed.
1. Determine calculation type (`static` or `relax`).
1. Collect only missing critical parameters.
1. Generate `INCAR` (with `KSPACING` policy by default).
1. Generate optional `KPOINTS` only when explicitly requested.
1. Provide `POTCAR` mapping and assembly instructions.
1. Return a handoff-ready task directory; if requested, hand off to `dpdisp-submit`.

## VASP parameters to collect

### Must provide

Do not generate a formal VASP task unless these are known or explicitly confirmed:

- `SYSTEM` label
- `ENCUT`
- k-point policy (`KSPACING` value by default, or explicit mesh)
- `ISMEAR` and `SIGMA` policy
- pseudopotential mapping for each element

### Usually should be explicit

These should normally be confirmed rather than guessed:

- `EDIFF`
- `NELM`
- `PREC`
- `LREAL`
- `ISPIN` and `MAGMOM` when relevant
- `IVDW` when dispersion may matter

### Task-specific additions

For `relax`:

- `IBRION`
- `NSW`
- `EDIFFG`
- `ISIF` relaxation mode (must match user intent)

## Relaxation policy (important)

`relax` must be classified by intent before setting `ISIF`:

- ion-only relaxation
- cell+ion relaxation
- low-dimensional/slab-style relaxation policy

Do not silently choose a relaxation mode when user intent is ambiguous.

For 2D/slab cases, explicitly confirm constraints and note assumptions in output.

## K-point policy

For this version:

- default path for `static`/`relax`: use `KSPACING` in `INCAR`
- `KPOINTS` file is optional and generated only when user explicitly requests manual mesh

## Required behavior

1. Inspect structure if accessible.
1. Determine element list, atom count, and lattice consistency.
1. Normalize to VASP-ready files when needed.
1. Confirm task type and relaxation intent.
1. Gather only missing critical settings.
1. Generate files and explain assumptions.
1. Flag unresolved scientific choices instead of hiding them.
1. Return exact output paths.

## Defaulting policy

Allowed only for low-risk, clearly labeled assumptions.

Reasonable provisional defaults:

- `static` for plain single-point requests
- conservative convergence defaults when user is indifferent
- `KSPACING`-driven sampling for `static`/`relax`

Do **not** silently invent:

- structure data
- pseudopotential files
- production `ENCUT` values
- magnetic state for potentially open-shell systems
- relaxation `ISIF` mode when intent is unclear

## Expected output

Provide:

1. generated file set (`POSCAR`, `INCAR`, optional `KPOINTS`)
1. `POTCAR` mapping/assembly instructions
1. short summary of chosen settings
1. explicit assumptions
1. unresolved decisions for user confirmation
1. handoff note to `dpdisp-submit` if execution is requested

## Minimal task layout

```text
vasp_task/
├── POSCAR
├── INCAR
├── KPOINTS   (optional)
└── POTCAR    (or assembly instructions)
```

## Handoff rule

When the user asks to submit the generated VASP task:

- finish generating the task directory and input files
- tell the user the task is ready
- hand off to `dpdisp-submit`

## Common failure points

- missing user-provided structure
- inconsistent lattice/cell for periodic systems
- invalid POTCAR mapping for elements
- poor `ENCUT` / k-point policy
- inappropriate smearing choices
- incorrect relaxation intent mapped to `ISIF`
