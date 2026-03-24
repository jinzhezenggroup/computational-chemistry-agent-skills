---
name: ase-workflows
description: Route ASE atomistic workflow requests to task-specific subskills based on user intent. Use when the user asks for ASE-based static, relaxation, MD, or NEB workflows and you must apply consistent workflow controls independent of calculator backend.
compatibility: Requires Python environment with ASE installed and at least one compatible ASE calculator backend.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://gitlab.com/ase/ase
---

# ASE Workflows Router

Use this skill as the top-level ASE workflow orchestration layer.

## Purpose

This skill routes requests to one task-specific workflow subskill path:

- `ase/ase-workflows/static`
- `ase/ase-workflows/relax`
- `ase/ase-workflows/md`
- `ase/ase-workflows/neb`

## Scope

This router skill should:

- classify user intent into one ASE workflow type
- collect minimal task context (goal, convergence target, outputs)
- delegate detailed workflow controls to selected subskill
- request calculator backend via `ase/ase-calculators` router
- enforce consistent output/handoff policy

This router skill should not:

- hardcode backend-specific calculator parameters
- execute or submit calculations directly

## Routing rules

1. single-point energy/force/stress -> `ase/ase-workflows/static`
1. geometry optimization -> `ase/ase-workflows/relax`
1. finite-temperature trajectory -> `ase/ase-workflows/md`
1. reaction path / transition-state pathway -> `ase/ase-workflows/neb`

If intent is ambiguous, ask one focused clarification question.

## Shared policy for all workflow subskills

- separate workflow logic from backend adapter logic
- expose assumptions and unresolved choices
- return reproducible task layout and run script
- if execution is requested, hand off to `dpdisp-submit`

## Output from router

Provide:

1. selected workflow subskill path
1. why it was selected
1. missing minimum inputs (if any)
1. explicit next step (invoke selected subskill)
