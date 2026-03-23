---
name: dft-vasp
description: Route VASP DFT requests to task-specific subskills based on user intent. Use when the user asks for VASP workflows and you must decide between static SCF, relaxation, DOS, or band-structure task preparation. This orchestration skill does not own detailed input generation logic; it dispatches to the correct VASP subskill and enforces consistent handoff to submission skills.
compatibility: Requires a user-provided structure and valid VASP pseudopotential resources/license in the target environment.
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.2.0
  repository: https://vasp.at/
---

# VASP Task Router

Use this skill as the **top-level VASP orchestration layer**.

## Purpose

This skill routes the request to one task-specific VASP subskill path:

- `dft-vasp/static`
- `dft-vasp/relax`
- `dft-vasp/dos`
- `dft-vasp/band`

## Scope

This router skill should:

- require a user-provided structure or prerequisite run artifacts
- classify user intent into one VASP task type
- collect only minimal shared context before dispatch
- delegate detailed parameter handling to the selected subskill
- enforce consistent output/handoff policy across subskills

This router skill should **not**:

- own full INCAR/KPOINTS templates for all tasks
- execute or submit calculations
- bypass task-specific guardrails

## Hard requirement

The user must provide enough starting context:

- structure input for `static` / `relax`
- prerequisite SCF artifacts for `dos` / `band` when required

If prerequisites are missing, stop and ask for them.

## Routing rules

1. If user requests single-point energy/electronic SCF: route to `dft-vasp/static`.
1. If user requests geometry optimization: route to `dft-vasp/relax`.
1. If user requests density of states workflow: route to `dft-vasp/dos`.
1. If user requests band-structure workflow: route to `dft-vasp/band`.
1. If intent is ambiguous, ask one focused clarification question before routing.

## Shared policy for all subskills

- do not invent pseudopotentials
- expose assumptions explicitly
- report unresolved scientific choices
- return handoff-ready task directory
- if execution is requested, hand off to `dpdisp-submit`

## Output from router

Provide:

1. selected subskill name
1. why it was selected
1. minimal required inputs still missing (if any)
1. explicit next step (invoke selected subskill)
