---
name: static
description: Prepare DFTB+ single-point (static) task inputs from a user-provided structure and essential SCC/settings choices. Use when the user needs total-energy/electronic single-point evaluation.
compatibility: Requires a user-provided structure, valid Slater-Koster parameter files, and runnable DFTB+ environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://github.com/dftbplus/dftbplus
---

# DFTB+ Static (Subskill)

## Scope

This skill prepares static tasks only.

It should generate:

- geometry input
- `dftb_in.hsd` for static SCC/non-SCC run
- output/restart naming policy

It should not submit or execute jobs.

## Must provide

- structure input
- SK parameter set choice
- SCC policy (`SCC`/non-`SCC`) and convergence settings
- k-point policy for periodic systems

## Usually should be explicit

- charge/spin setup when relevant
- mixer/max-iteration/tolerance settings
- dispersion/third-order corrections when relevant

## Expected output

1. static-task input/script layout
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
