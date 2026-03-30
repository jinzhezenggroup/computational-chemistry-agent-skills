---
name: dft-gpaw
description: Route GPAW DFT requests to task-specific subskills based on user intent. Use when the user asks for GPAW workflows and you must decide between static SCF, relaxation, DOS, or band-structure task preparation. This orchestration skill dispatches to the correct GPAW subskill and enforces consistent handoff to submission skills.
compatibility: Requires a user-provided structure and a runnable GPAW Python environment (with ASE/GPAW) in the target runtime.
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/gpaw/gpaw
---

# GPAW Task Router

Use this skill as the **top-level GPAW orchestration layer**.

## Purpose

This skill routes requests to one task-specific GPAW subskill path:

- `dft-gpaw/static`
- `dft-gpaw/relax`
- `dft-gpaw/dos`
- `dft-gpaw/band`

## Scope

This router skill should:

- require a user-provided structure or prerequisite run context
- classify request intent into one GPAW task type
- collect minimal shared context before dispatch
- delegate detailed parameter handling to the selected subskill
- enforce consistent output/handoff policy across subskills

This router skill should **not**:

- own full task-specific Python templates for all cases
- execute or submit calculations
- bypass subskill-specific guardrails

## Hard requirement

The user must provide enough starting context:

- structure input for `static` / `relax`
- prerequisite ground-state context for `dos` / `band`

If prerequisites are missing, stop and ask for them.

## Routing rules

1. If user requests single-point SCF/energy: route to `dft-gpaw/static`.
1. If user requests geometry optimization: route to `dft-gpaw/relax`.
1. If user requests DOS workflow: route to `dft-gpaw/dos`.
1. If user requests band-structure workflow: route to `dft-gpaw/band`.
1. If intent is ambiguous, ask one focused clarification question before routing.

## Shared policy for all subskills

- do not invent missing physical parameters
- do not fabricate restart context/results
- expose assumptions explicitly
- return handoff-ready task layout
- if execution is requested, hand off to `dpdisp-submit`

## Output from router

Provide:

1. selected subskill path
1. why it was selected
1. minimal missing inputs (if any)
1. explicit next step (invoke selected subskill)
