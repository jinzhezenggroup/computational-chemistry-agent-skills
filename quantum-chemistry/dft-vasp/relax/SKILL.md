---
name: relax
description: Prepare VASP geometry-relaxation input tasks from a user-provided structure and essential DFT settings. Use when the user needs ionic or cell-coupled relaxation and requires explicit ISIF-driven relaxation intent mapping, INCAR generation, and POTCAR mapping instructions.
compatibility: Requires a user-provided structure and valid VASP pseudopotential resources/license in the target environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://vasp.at/
---

# VASP Relaxation (Subskill)

## Scope

This skill prepares relaxation tasks only.

It should generate:

- `POSCAR`
- `INCAR`
- optional `KPOINTS`
- POTCAR mapping/assembly instructions

It should not submit or execute jobs.

## Relaxation intent is mandatory

Before assigning `ISIF`, classify user intent:

- ion-only relaxation
- cell+ion relaxation
- low-dimensional/slab-style relaxation policy

If intent is ambiguous, ask for clarification.

## Must provide

- structure input
- `ENCUT`
- `ISMEAR` / `SIGMA`
- relaxation controls: `IBRION`, `NSW`, `EDIFFG`, `ISIF`
- k-point policy (`KSPACING` default or explicit mesh)
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
- generate `KPOINTS` only when explicit manual mesh is requested

## Expected output

1. task directory with generated input files
1. explicit `ISIF` selection rationale
1. settings summary and assumptions
1. unresolved choices for user confirmation
1. handoff note to `dpdisp-submit` if execution is requested
