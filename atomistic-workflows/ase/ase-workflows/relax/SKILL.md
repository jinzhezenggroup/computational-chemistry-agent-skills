---
name: relax
description: Prepare ASE geometry-optimization workflow tasks with backend-agnostic controls. Use when the user needs structural relaxation while selecting optimizer, convergence target, constraints, and output trajectory policy independently of calculator backend.
compatibility: Requires ASE and a configured backend adapter from `ase/ase-calculators`.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE Relax Workflow (Subskill)

## Scope

This subskill prepares relaxation workflow tasks only.

It should generate:

- optimizer workflow script (`BFGS`/`FIRE` etc.)
- convergence policy (`fmax`, max steps)
- constraints and trajectory/log policy

## Must provide

- structure input
- selected backend adapter
- optimizer choice
- force threshold and step limits

## Usually should be explicit

- fixed-atom/layer constraints
- stress-aware relaxation policy
- restart behavior

## Expected output

1. relax workflow script/layout
1. optimizer/convergence summary
1. assumptions and unresolved choices
1. handoff note to `dpdisp-submit` if execution is requested
