---
name: md
description: Prepare ASE molecular-dynamics workflow tasks with backend-agnostic controls. Use when the user needs finite-temperature trajectories with explicit ensemble, timestep, thermostat, and output policies.
compatibility: Requires ASE and a configured backend adapter from `ase/ase-calculators`.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://gitlab.com/ase/ase
---

# ASE MD Workflow (Subskill)

## Scope

This subskill prepares MD workflow tasks only.

It should generate:

- ASE MD workflow script
- ensemble/integrator/thermostat settings
- trajectory/output policy

## Must provide

- structure input
- selected backend adapter
- timestep and number of steps
- ensemble intent and temperature policy

## Usually should be explicit

- pressure/barostat policy when relevant
- initial velocity policy
- checkpoint/restart policy

## Expected output

1. MD workflow script/layout
1. MD control summary
1. assumptions and unresolved choices
1. handoff note to `dpdisp-submit` if execution is requested
