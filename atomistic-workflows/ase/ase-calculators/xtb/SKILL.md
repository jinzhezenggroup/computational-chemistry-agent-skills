---
name: xtb
description: Configure ASE xTB calculator adapter settings for ASE workflows. Use when ASE workflow tasks require xTB backend setup including method, charge/spin, solvent, and stress-capability choices.
compatibility: Requires ASE, the xtb Python package, and an xTB runtime supported by the Python package.
license: MIT
catalog-hidden: true
metadata:
  author: qqgu
  version: 0.1.0
  repository: https://gitlab.com/ase/ase
---

# ASE xTB Adapter (Subskill)

## Scope

This adapter configures xTB backend parameters for ASE workflows.

It should return calculator configuration, not workflow logic.

For broader xTB usage patterns, including direct ASE scripts and dpdata bridges, defer to `quantum-chemistry/xtb`.

## Must provide

- xTB method (`GFN2-xTB`, `GFN1-xTB`, or `GFN0-xTB`)
- charge and spin assumptions
- solvent model choice, if requested
- stress requirement check (`GFN0-xTB` only through the ASE bridge)

## Usually should be explicit

- whether the workflow needs energies only, energies plus forces, or stress
- geometry optimization force threshold and step limit when handed to an ASE workflow
- output/checkpoint files owned by the workflow layer

## Expected output

1. calculator configuration payload
1. backend assumptions and prerequisites
1. unresolved backend choices

## Minimal calculator payload

```python
from xtb.ase.calculator import XTB

calculator = XTB(method="GFN2-xTB")
```

Return the `calculator` object to the requesting ASE workflow layer instead of running the workflow here.
