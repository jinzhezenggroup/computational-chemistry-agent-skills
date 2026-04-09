# Commands and Workflow

Use this reference for `ase/ase-calculators` routing.

## Router role

`ase/ase-calculators` dispatches to one adapter path:

- `ase/ase-calculators/gpaw`
- `ase/ase-calculators/mace`
- `ase/ase-calculators/xtb`

## Dispatch checklist

1. identify backend target
1. validate environment prerequisites
1. apply backend adapter defaults/policies
1. return calculator configuration to `ase/ase-workflows`

## Example handoff payload

- backend: `gpaw`, `mace`, or `xtb`
- calculator mode/settings
- device/precision policy or xTB method/solvent policy
- restart/checkpoint policy
