---
name: mace
description: Configure ASE MACE calculator adapter settings for ASE workflows. Use when ASE workflow tasks require MACE backend setup including model path/version, device/precision, stress availability, and inference controls.
compatibility: Requires ASE, MACE dependencies, and an available MACE model checkpoint.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE MACE Adapter (Subskill)

## Scope

This adapter configures MACE backend parameters for ASE workflows.

It should return calculator configuration, not workflow logic.

## Must provide

- model checkpoint/path
- device policy (`cpu`/`cuda`)
- precision policy
- stress/force capability requirements

## Usually should be explicit

- batch/inference tuning
- model domain applicability note
- restart/checkpoint policy

## Expected output

1. calculator configuration payload
1. backend assumptions and prerequisites
1. unresolved backend choices
