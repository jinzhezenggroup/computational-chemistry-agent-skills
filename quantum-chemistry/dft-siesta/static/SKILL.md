---
name: static
description: Prepare SIESTA single-point (static) task inputs from a user-provided structure and essential DFT settings. Use when the user needs total-energy/electronic SCF evaluation with explicit SIESTA mesh, basis, and SCF controls.
compatibility: Requires a user-provided structure, compatible pseudopotentials, and runnable SIESTA environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://gitlab.com/siesta-project/siesta
---

# SIESTA Static (Subskill)

## Scope

This skill prepares static tasks only.

It should generate:

- SIESTA input (for example `.fdf`)
- pseudopotential mapping summary
- output/restart naming policy

It should not submit or execute jobs.

## Must provide

- structure input
- XC functional choice
- basis quality policy
- mesh cutoff and SCF convergence policy
- k-point policy for periodic systems

## Usually should be explicit

- charge/spin setup
- mixing/iteration controls
- electronic temperature/smearing policy when relevant

## Expected output

1. static-task input layout
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
