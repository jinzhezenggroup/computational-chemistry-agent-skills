---
name: static
description: Prepare VASP static SCF input tasks from a user-provided structure and essential DFT settings. Use when the user needs single-point electronic structure/total-energy calculations with INCAR generation, KSPACING-based k-point policy (or explicit KPOINTS on request), and POTCAR mapping instructions.
compatibility: Requires a user-provided structure and valid VASP pseudopotential resources/license in the target environment.
catalog-hidden: true
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://vasp.at/
---

# VASP Static SCF (Subskill)

## Scope

This skill prepares static SCF tasks only.

It should generate:

- `POSCAR`
- `INCAR`
- optional `KPOINTS` (manual mesh only when requested)
- POTCAR mapping/assembly instructions

It should not submit or execute jobs.

## Must provide

- structure input
- `ENCUT`
- k-point policy (`KSPACING` default or explicit mesh)
- `ISMEAR` / `SIGMA`
- POTCAR mapping for each element

## Usually should be explicit

- `EDIFF`
- `NELM`
- `PREC`
- `LREAL`
- `ISPIN` / `MAGMOM` when relevant
- `IVDW` when relevant

## K-point policy

- default: `KSPACING` in `INCAR`
- generate `KPOINTS` only when user asks for explicit mesh

## Expected output

1. task directory with generated input files
1. settings summary and assumptions
1. unresolved choices for user confirmation
1. handoff note to `dpdisp-submit` if execution is requested
