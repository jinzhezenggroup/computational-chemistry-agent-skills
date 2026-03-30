---
name: static
description: Prepare CP2K single-point (static) task inputs from a user-provided structure and essential DFT settings. Use when the user needs total-energy/electronic SCF evaluation with explicit CP2K basis/potential and SCF controls.
compatibility: Requires a user-provided structure, suitable CP2K basis/potential files, and runnable CP2K environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/cp2k/cp2k
---

# CP2K Static (Subskill)

## Scope

This skill prepares static tasks only.

It should generate:

- CP2K input (`.inp`) for static SCF
- basis/potential mapping summary
- output/restart naming policy

It should not submit or execute jobs.

## Must provide

- structure input
- XC functional choice
- basis/potential set choice
- SCF convergence policy
- k-point or periodicity policy when relevant

## Usually should be explicit

- charge/spin setup
- cutoff/rel_cutoff/mgrid policy
- smearing/occupation policy for metallic systems

## Expected output

1. static-task input layout
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
