# Commands and Workflow

Use this reference for practical xTB command and script patterns.

## 1. Minimal single-point energy with the ASE bridge

Recommended ad hoc command:

```bash
uv run --no-project --with ase --with xtb --with typing_extensions python h2o_xtb_sp.py
```

Example script:

```python
from ase.build import molecule
from xtb.ase.calculator import XTB

atoms = molecule("H2O")
atoms.calc = XTB(method="GFN2-xTB")

print("energy_eV=", atoms.get_potential_energy())
print("forces_shape=", atoms.get_forces().shape)
print("charges=", atoms.get_charges())
```

Use this pattern when the user wants the quickest reproducible xTB energy/force evaluation from Python.

## 2. Geometry optimization with ASE + xTB

Recommended ad hoc command:

```bash
uv run --no-project --with ase --with xtb --with typing_extensions python relax_xtb.py
```

Example script:

```python
from ase.build import molecule
from ase.optimize import BFGS
from xtb.ase.calculator import XTB

atoms = molecule("H2O")
atoms.calc = XTB(method="GFN2-xTB")

opt = BFGS(atoms, trajectory="opt.traj", logfile="opt.log")
opt.run(fmax=0.05, steps=200)

print("final_energy_eV=", atoms.get_potential_energy())
print("final_positions=\n", atoms.get_positions())
```

Use this pattern when the user asks for xTB geometry optimization but prefers an ASE Python workflow.

## 3. Label structures with dpdata driver + xTB

Recommended ad hoc command:

```bash
uv run --no-project --with dpdata --with ase --with xtb --with typing_extensions python dpdata_xtb_label.py
```

Example script:

```python
import numpy as np
from dpdata.system import System
from xtb.ase.calculator import XTB

sys = System("input.xyz", fmt="xyz")
ls = sys.predict(driver="ase", calculator=XTB(method="GFN2-xTB"))

print("energies=", ls.data["energies"])
print("forces_shape=", np.array(ls.data["forces"]).shape)
```

Use this pattern when the user wants xTB-labeled energies/forces in dpdata workflows.

## 4. Minimize structures with dpdata minimizer + xTB

Recommended ad hoc command:

```bash
uv run --no-project --with dpdata --with ase --with xtb --with typing_extensions python dpdata_xtb_minimize.py
```

Example script:

```python
import numpy as np
from dpdata.driver import Driver
from dpdata.system import System
from xtb.ase.calculator import XTB

sys = System("input.xyz", fmt="xyz")
ase_driver = Driver.get_driver("ase")(calculator=XTB(method="GFN2-xTB"))
ls = sys.minimize(minimizer="ase", driver=ase_driver, fmax=0.05, max_steps=200)

print("energies=", ls.data["energies"])
print("coords_shape=", np.array(ls.data["coords"]).shape)
```

Use this pattern when the user wants xTB-driven geometry minimization but wants the result as a dpdata labeled system.

## Notes and pitfalls

- Prefer `uv run`, not `uvx`, for these Python-script patterns.
- The package name is `xtb`, not `xtb-python`.
- If import fails with `ModuleNotFoundError: typing_extensions`, add `--with typing_extensions` explicitly.
- `stress` support through the ASE bridge is limited to `GFN0-xTB`.
