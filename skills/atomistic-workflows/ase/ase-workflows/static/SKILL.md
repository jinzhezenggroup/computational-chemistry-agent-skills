---
name: static
description: Prepare ASE static (single-point) workflow tasks with backend-agnostic workflow controls. Use when the user needs one-shot energy/force/stress evaluation through an ASE calculator adapter.
compatibility: Requires ASE and a configured backend adapter from `ase/ase-calculators`.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE Static Workflow (Subskill)

## Scope

This subskill prepares static workflow tasks only.

It should generate:

- workflow script/layout for single-point evaluation
- standardized output policy (energy/forces/stress)
- backend adapter integration points

## Must provide

- structure input
- selected backend adapter
- requested properties (energy/force/stress)

## Expected output

1. static workflow script/layout
1. requested-property checklist
1. assumptions and unresolved choices
1. handoff note to `dpdisp-submit` if execution is requested
