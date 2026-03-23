---
name: dos
description: Prepare GPAW DOS workflow scripts from existing ground-state context and user-specified DOS settings. Use when the user requests total/projected DOS setup with explicit prerequisite checks against prior converged calculations.
compatibility: Requires prerequisite ground-state context and runnable GPAW+ASE Python environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/gpaw/gpaw
---

# GPAW DOS Preparation (Subskill)

## Scope

This skill prepares DOS-stage tasks only.

It should:

- verify prerequisite ground-state context
- prepare DOS script/settings
- report assumptions and unresolved choices

It should not submit or execute jobs.

## Prerequisites

Require explicit prior converged ground-state context (restart/checkpoint and compatible settings).

If prerequisites are missing, stop and ask for them.

## Must provide

- source ground-state context path
- DOS intent (`total` or `projected`)
- energy-window / broadening policy
- k-point/density policy for DOS stage

## Usually should be explicit

- projection channel choices
- smearing/broadening parameters
- output grid resolution

## Expected output

1. DOS-stage script/input updates
1. prerequisite check summary
1. settings summary and assumptions
1. handoff note to `dpdisp-submit` if execution is requested
