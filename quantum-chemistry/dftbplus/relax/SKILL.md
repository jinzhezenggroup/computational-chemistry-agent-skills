---
name: relax
description: Prepare DFTB+ geometry-relaxation task inputs from a user-provided structure and optimization settings. Use when the user needs ion-only or cell-coupled structural optimization.
compatibility: Requires a user-provided structure, valid Slater-Koster parameter files, and runnable DFTB+ environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/dftbplus/dftbplus
---

# DFTB+ Relax (Subskill)

## Scope

This skill prepares relaxation tasks only.

It should generate:

- geometry input
- relaxation-capable `dftb_in.hsd`
- explicit optimizer/convergence controls

It should not submit or execute jobs.

## Relax intent is mandatory

Before preparing inputs, classify intent:

- ion-only relaxation
- cell+ion relaxation
- constrained relaxation (e.g., slab constraints)

If intent is ambiguous, ask for clarification.

## Must provide

- structure input
- SK parameter set choice
- optimizer settings and convergence target
- SCC and k-point policies

## Usually should be explicit

- stress/cell update policy
- fixed-atom/layer constraints
- charge/spin initialization when relevant

## Expected output

1. relaxation-task input/script layout
1. explicit relaxation-policy rationale
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
