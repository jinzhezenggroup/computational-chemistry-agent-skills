---
name: ase-calculators
description: Route ASE calculator-backend requests to adapter subskills based on backend choice. Use when ASE workflows need backend-specific calculator setup (for example GPAW, MACE, or xTB) while keeping workflow logic backend-agnostic.
compatibility: Requires Python environment with ASE and selected backend packages installed.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE Calculators Router

Use this skill as the top-level ASE calculator adapter layer.

## Purpose

This skill routes backend selection to one adapter subskill path:

- `ase/ase-calculators/gpaw`
- `ase/ase-calculators/mace`
- `ase/ase-calculators/xtb`

## Scope

This router skill should:

- identify backend requested by user or workflow
- verify minimum backend prerequisites
- delegate backend-specific calculator configuration
- return adapter configuration summary to workflow layer

This router skill should not:

- own workflow-level logic (`relax`, `md`, `neb` controls)
- execute calculations directly

## Routing rules

1. GPAW backend requested -> `ase/ase-calculators/gpaw`
1. MACE backend requested -> `ase/ase-calculators/mace`
1. xTB backend requested -> `ase/ase-calculators/xtb`
1. if backend unspecified, propose options and ask one focused question

## Shared output contract

Return:

1. selected adapter path
1. backend configuration summary
1. unresolved backend prerequisites
