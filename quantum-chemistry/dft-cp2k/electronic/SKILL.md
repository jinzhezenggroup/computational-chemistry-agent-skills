---
name: electronic
description: Prepare CP2K electronic-analysis task inputs from prior converged context. Use when the user requests post-ground-state electronic analyses and needs prerequisite-aware setup.
compatibility: Requires prior converged CP2K context, suitable basis/potential files, and runnable CP2K environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/cp2k/cp2k
---

# CP2K Electronic Analysis (Subskill)

## Scope

This skill prepares post-ground-state electronic-analysis tasks.

It should:

- verify prerequisite converged context
- prepare analysis-specific input controls
- report assumptions and unresolved choices

It should not submit or execute jobs.

## Prerequisites

Require explicit prior converged context compatible with requested analysis.

If prerequisites are missing, stop and ask for them.

## Must provide

- source context path
- analysis intent (for example DOS/PDOS/band-like workflow)
- mesh/path/resolution policy as applicable

## Usually should be explicit

- projection settings
- broadening/plotting policy
- export format expectations

## Expected output

1. analysis-stage input updates
1. prerequisite check summary
1. settings summary and assumptions
1. handoff note to `dpdisp-submit` if execution is requested
