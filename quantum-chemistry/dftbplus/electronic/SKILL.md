---
name: electronic
description: Prepare DFTB+ electronic-analysis task inputs based on prior ground-state context. Use when the user requests band/DOS-style analyses and needs prerequisite-aware setup.
compatibility: Requires prior ground-state context, valid Slater-Koster parameter files, and runnable DFTB+ environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://github.com/dftbplus/dftbplus
---

# DFTB+ Electronic Analysis (Subskill)

## Scope

This skill prepares post-ground-state electronic-analysis tasks.

It should:

- verify prerequisite context
- prepare analysis-specific input controls
- report assumptions and unresolved choices

It should not submit or execute jobs.

## Prerequisites

Require explicit prior converged context compatible with requested analysis.

If prerequisites are missing, stop and ask for them.

## Must provide

- source context path
- analysis intent (`band`, `dos`, or both)
- path/mesh policy as applicable
- resolution/broadening policy

## Usually should be explicit

- k-path convention source
- projection settings if needed
- output format expectations

## Expected output

1. analysis-stage input/script updates
1. prerequisite check summary
1. settings summary and assumptions
1. handoff note to `dpdisp-submit` if execution is requested
