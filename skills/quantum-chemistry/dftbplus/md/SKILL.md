---
name: md
description: Prepare DFTB+ molecular-dynamics task inputs from a user-provided structure and MD controls. Use when the user needs finite-temperature trajectories using DFTB+.
compatibility: Requires a user-provided structure, valid Slater-Koster parameter files, and runnable DFTB+ environment.
catalog-hidden: true
license: LGPL-3.0-or-later
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/dftbplus/dftbplus
---

# DFTB+ MD (Subskill)

## Scope

This skill prepares MD tasks only.

It should generate:

- MD-capable `dftb_in.hsd`
- thermostat/integrator controls
- trajectory/output policy

It should not submit or execute jobs.

## Must provide

- structure input
- SK parameter set choice
- timestep, number of steps, target ensemble intent
- temperature/thermostat policy
- SCC and k-point policies

## Usually should be explicit

- initial velocity policy
- output stride for energy/trajectory
- charge/spin policy when relevant

## Expected output

1. MD-task input/script layout
1. MD control summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
