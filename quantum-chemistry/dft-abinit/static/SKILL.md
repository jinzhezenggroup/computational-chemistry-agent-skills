---
name: static
description: Prepare ABINIT single-point (static) task inputs from a user-provided structure and essential DFT settings. Use when the user needs total-energy/electronic SCF evaluation with explicit ABINIT cutoff, k-point, and SCF controls.
compatibility: Requires a user-provided structure, suitable pseudopotentials, and runnable ABINIT environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/abinit/abinit
---

# ABINIT Static (Subskill)

## Scope

This skill prepares static tasks only.

It should generate:

- ABINIT input for static SCF
- pseudopotential mapping summary
- output/restart naming policy

It should not submit or execute jobs.

## Must provide

- structure input
- XC functional choice
- cutoff and k-point policy
- SCF convergence policy

## Usually should be explicit

- charge/spin setup
- smearing/occupancy policy for metallic systems
- mixing/iteration controls

## Expected output

1. static-task input layout
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
