---
name: static
description: Prepare GPAW static SCF task inputs/scripts from a user-provided structure and essential DFT settings. Use when the user needs single-point total-energy/electronic calculations with explicit GPAW calculator settings and reproducible run script layout.
compatibility: Requires a user-provided structure and runnable GPAW+ASE Python environment.
catalog-hidden: true
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/gpaw/gpaw
---

# GPAW Static SCF (Subskill)

## Scope

This skill prepares static SCF tasks only.

It should generate:

- structure input in backend-friendly format
- task Python script (ASE + GPAW setup)
- output/restart naming policy

It should not submit or execute jobs.

## Must provide

- structure input
- XC functional choice
- basis mode (`PW`/`LCAO`/`FD`) with key numerical settings
- k-point policy
- SCF convergence policy

## Usually should be explicit

- occupation/smearing settings
- spin mode (`spinpol`) and initial moments when relevant
- output checkpoints (for restart/post-processing)

## Expected output

1. static-task script/input layout
1. settings summary and assumptions
1. unresolved choices for user confirmation
1. handoff note to `dpdisp-submit` if execution is requested
