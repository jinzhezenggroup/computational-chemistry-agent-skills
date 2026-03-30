---
name: band
description: Prepare GPAW band-structure workflow scripts from existing ground-state context and user-specified k-path settings. Use when the user requests electronic band-structure calculations with explicit prerequisite checks and path-definition handling.
compatibility: Requires prerequisite ground-state context and runnable GPAW+ASE Python environment.
catalog-hidden: true
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/gpaw/gpaw
---

# GPAW Band Preparation (Subskill)

## Scope

This skill prepares band-structure-stage tasks only.

It should:

- verify prerequisite ground-state context
- generate or validate high-symmetry k-path settings
- prepare stage-appropriate script/settings
- report assumptions and unresolved choices

It should not submit or execute jobs.

## Prerequisites

Require explicit prior converged ground-state context and a clear path convention.

If prerequisites are missing, stop and ask for them.

## Must provide

- source ground-state context path
- k-path convention or explicit path
- points-per-segment / resolution policy
- band intent and output expectations

## Usually should be explicit

- symmetry/path generator source
- spin/channel projection expectations
- plotting/export format expectations

## Expected output

1. band-stage script/input updates
1. k-path summary
1. prerequisite check summary
1. settings summary and assumptions
1. handoff note to `dpdisp-submit` if execution is requested
