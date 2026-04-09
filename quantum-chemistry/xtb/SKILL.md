---
name: xtb
description: Prepare and explain xTB semiempirical quantum-chemistry workflows for single-point energy, forces, charges, dipole, geometry optimization, and molecular dynamics. Use when the user asks for xTB calculations directly, or wants to use xTB through Python/ASE/dpdata bridges while keeping xTB as the primary method rather than as an ASE-only backend.
compatibility: Requires a runnable xTB environment. Python-based workflows can use the `xtb` package; for reproducible ad hoc runs with uv, prefer `uv run --no-project --with ase --with xtb --with typing_extensions python ...` when using the ASE bridge.
license: LGPL-3.0-or-later
metadata:
  author: njzjz-bot
  version: '1.0'
  repository: https://github.com/grimme-lab/xtb-python
---

# xTB

Use this skill as the **top-level xTB orchestration layer**.

## Scope

This skill should:

- identify whether the user wants direct xTB usage or a Python bridge workflow
- classify the task as static, optimization, or MD-style usage
- keep xTB as the primary method in the user-facing framing
- provide runnable examples for direct Python/ASE integration when appropriate
- document how to connect xTB to dpdata driver/minimizer flows

This skill should **not**:

- force the user into ASE if they asked for xTB itself
- hide xTB-specific scientific choices behind generic backend wording
- submit jobs directly; use `dpdisp-submit` if execution/submission is requested

## Supported usage patterns

### 1. Direct xTB-oriented tasks

Use this skill when the user asks for:

- xTB single-point energy
- xTB forces / charges / dipole
- xTB geometry optimization
- xTB molecular dynamics
- xTB method choice such as `GFN0-xTB`, `GFN1-xTB`, or `GFN2-xTB`
- xTB solvent settings

### 2. xTB through the ASE bridge

If the user wants Python scripting, ASE integration, or ASE workflows, use:

```python
from xtb.ase.calculator import XTB
```

Treat ASE as an integration layer, not the primary identity of the method.

### 3. xTB through dpdata

If the user wants labeled data or geometry minimization through dpdata, bridge via the ASE driver/minimizer while still presenting xTB as the force/energy method.

## Practical installation notes

For one-off Python scripts, prefer `uv run` instead of `uvx` because this is a Python package used inside a Python script, not a standalone CLI tool.

Recommended pattern for the ASE bridge:

```bash
uv run --no-project --with ase --with xtb --with typing_extensions python your_script.py
```

Notes:

- The PyPI package name is `xtb`.
- The upstream docs/project are often referred to as `xtb-python`.
- If `ModuleNotFoundError: typing_extensions` appears, add `--with typing_extensions` explicitly.

## Method selection guidance

- `GFN2-xTB`: default choice for most molecular single-point and force evaluations
- `GFN1-xTB`: use when there is a user or literature reason
- `GFN0-xTB`: use when the workflow specifically needs xTB-level stress through the ASE bridge

## ASE bridge example

```python
from ase.build import molecule
from xtb.ase.calculator import XTB

atoms = molecule("H2O")
atoms.calc = XTB(method="GFN2-xTB")
print(atoms.get_potential_energy())
print(atoms.get_forces())
print(atoms.get_charges())
```

Common calculator arguments:

- `method`
- `accuracy`
- `electronic_temperature`
- `max_iterations`
- `solvent`
- `cache_api`

Property support through the ASE bridge includes:

- `energy` / `free_energy`
- `forces`
- `dipole`
- `charges`
- `stress` for `GFN0-xTB` only

## dpdata driver bridge

If the user wants dpdata labeling:

```python
from dpdata.system import System
from xtb.ase.calculator import XTB

sys = System("input.xyz", fmt="xyz")
ls = sys.predict(driver="ase", calculator=XTB(method="GFN2-xTB"))
```

This connects naturally to `tools/dpdata-driver`.

## dpdata minimizer bridge

If the user wants dpdata geometry minimization:

```python
from dpdata.driver import Driver
from dpdata.system import System
from xtb.ase.calculator import XTB

sys = System("input.xyz", fmt="xyz")
ase_driver = Driver.get_driver("ase")(calculator=XTB(method="GFN2-xTB"))
ls = sys.minimize(minimizer="ase", driver=ase_driver, fmax=0.05, max_steps=200)
```

This connects naturally to `tools/dpdata-minimizer`.

## Output expectations

Provide:

1. the selected xTB usage mode
1. runnable command or script pattern
1. method/solvent/accuracy assumptions
1. unresolved scientific choices
1. handoff to `dpdisp-submit` if execution/submission is requested
