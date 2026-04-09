---
name: ase
description: Unified ASE router skill with a tree of subskills for static/relax/MD/NEB workflows and backend adapters (GPAW, MACE, xTB). Use when you need backend-agnostic workflow orchestration while keeping calculator-specific setup isolated in adapter subskills, with reproducible task preparation as output.
compatibility: Requires Python and ASE. Optional backend dependencies depend on the selected adapter such as GPAW, MACE, or xTB. Prepares tasks/configuration only; submit and run via dpdisp-submit when execution is requested.
license: MIT
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE Top-Level Router

Use this skill as the unified entry point for ASE ecosystem tasks.

## Purpose

This skill routes requests to one branch under the ASE tree:

- `ase/ase-workflows`
- `ase/ase-calculators`

## Scope

This top-level router should:

- decide whether the request is workflow-level or backend-adapter-level
- gather the minimum context required for the selected branch
- delegate details to the corresponding branch router
- keep workflow logic and backend logic separated

This top-level router should not:

- hardcode task-specific or backend-specific parameters directly
- execute calculations directly

## Routing rules

1. task intent is static/relax/md/neb workflow -> `ase/ase-workflows`
1. task intent is backend selection/configuration -> `ase/ase-calculators`
1. if mixed request, route to `ase/ase-workflows` first, then call `ase/ase-calculators` as dependency

## Output from top-level router

Provide:

1. selected ASE branch path
1. reason for branch selection
1. missing minimum inputs
1. explicit next delegation step
