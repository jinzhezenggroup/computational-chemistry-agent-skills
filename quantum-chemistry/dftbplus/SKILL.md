---
name: dftbplus
description: Route DFTB+ requests to task-specific subskills based on user intent. Use when the user asks for DFTB+ workflows and you must decide between static, relaxation, molecular dynamics, or electronic-structure post-ground-state preparation. This orchestration skill dispatches to the correct subskill and enforces consistent handoff to submission skills.
compatibility: Requires a runnable DFTB+ environment with suitable Slater-Koster parameter sets for the target elements.
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/dftbplus/dftbplus
---

# DFTB+ Task Router

Use this skill as the **top-level DFTB+ orchestration layer**.

## Purpose

This skill routes requests to one task-specific subskill path:

- `dftbplus/static`
- `dftbplus/relax`
- `dftbplus/md`
- `dftbplus/electronic`

## Scope

This router skill should:

- require a user-provided structure or prerequisite context
- classify request intent into one DFTB+ task type
- collect minimal shared context before dispatch
- delegate detailed parameter handling to selected subskill
- enforce consistent output/handoff policy across subskills

This router skill should **not**:

- own detailed input templates for all tasks
- execute or submit calculations
- bypass task-specific guardrails

## Hard requirement

The user must provide enough starting context:

- structure input for `static` / `relax` / `md`
- prerequisite ground-state context for `electronic`

If prerequisites are missing, stop and ask for them.

## Routing rules

1. If user requests single-point energy/electronic SCF: route to `dftbplus/static`.
1. If user requests geometry optimization: route to `dftbplus/relax`.
1. If user requests molecular dynamics: route to `dftbplus/md`.
1. If user requests band/DOS-style electronic analysis workflow: route to `dftbplus/electronic`.
1. If intent is ambiguous, ask one focused clarification question before routing.

## Shared policy for all subskills

- do not invent missing SK parameter files
- expose assumptions and unresolved scientific choices explicitly
- return handoff-ready task layout
- if execution is requested, hand off to `dpdisp-submit`

## Output from router

Provide:

1. selected subskill path
1. why it was selected
1. minimal missing inputs (if any)
1. explicit next step (invoke selected subskill)
