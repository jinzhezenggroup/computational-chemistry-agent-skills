---
name: relax
description: Prepare CP2K geometry-relaxation task inputs from a user-provided structure and optimization settings. Use when the user needs ion-only or cell-coupled optimization with explicit optimizer and convergence controls.
compatibility: Requires a user-provided structure, suitable CP2K basis/potential files, and runnable CP2K environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/cp2k/cp2k
---

# CP2K Relax (Subskill)

## Scope

This skill prepares relaxation tasks only.

It should generate:

- relaxation-capable CP2K input
- optimizer and convergence controls
- constraint policy when relevant

It should not submit or execute jobs.

## Relax intent is mandatory

Before preparing inputs, classify intent:

- ion-only relaxation
- cell+ion relaxation
- constrained relaxation (for example slab constraints)

If intent is ambiguous, ask for clarification.

## Must provide

- structure input
- basis/potential set choice
- optimizer and convergence thresholds
- stress/cell relaxation policy when applicable

## Usually should be explicit

- fixed atom/layer constraints
- charge/spin setup
- cutoff/grid and SCF policy

## Expected output

1. relaxation-task input layout
1. explicit relaxation-policy rationale
1. settings summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
