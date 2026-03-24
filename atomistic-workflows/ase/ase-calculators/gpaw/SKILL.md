---
name: gpaw
description: Configure ASE GPAW calculator adapter settings for ASE workflows. Use when ASE workflow tasks require GPAW backend setup including mode, k-point, convergence, and restart policies.
compatibility: Requires ASE, GPAW, and a runnable GPAW Python environment.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: '0.1.0'
  repository: https://gitlab.com/ase/ase
---

# ASE GPAW Adapter (Subskill)

## Scope

This adapter configures GPAW backend parameters for ASE workflows.

It should return calculator configuration, not workflow logic.

## Must provide

- GPAW mode (`PW` / `LCAO` / `FD`)
- XC choice
- k-point policy
- convergence controls

## Usually should be explicit

- occupation/smearing policy
- spin setup
- restart/checkpoint policy

## Expected output

1. calculator configuration payload
1. backend assumptions and prerequisites
1. unresolved backend choices
