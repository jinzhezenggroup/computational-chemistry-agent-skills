---
name: md
description: Prepare CP2K molecular-dynamics task inputs from a user-provided structure and MD controls. Use when the user needs finite-temperature trajectories with explicit ensemble, timestep, and thermostat/barostat settings.
compatibility: Requires a user-provided structure, suitable CP2K basis/potential files, and runnable CP2K environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://github.com/cp2k/cp2k
---

# CP2K MD (Subskill)

## Scope

This skill prepares MD tasks only.

It should generate:

- MD-capable CP2K input
- ensemble/integrator/thermostat controls
- trajectory/output policy

It should not submit or execute jobs.

## Must provide

- structure input
- basis/potential set choice
- timestep and number of steps
- ensemble intent (`NVE`/`NVT`/`NPT`)
- temperature/pressure control policy

## Usually should be explicit

- initial velocity policy
- output stride for energies/trajectory
- charge/spin and SCF policy

## Expected output

1. MD-task input layout
1. MD control summary and assumptions
1. unresolved choices for confirmation
1. handoff note to `dpdisp-submit` if execution is requested
