# ASE and dpdata Recipes

## ASE Single Point

```python
from ase.build import molecule
from xtbloom.ase import XTBloom

atoms = molecule("H2O")  # ASE coordinates are angstrom.
calculator = XTBloom(
    method="GFN2-xTB",
    backend="cpu",
    charge=0,
    multiplicity=1,
    warm_start=False,
)
atoms.calc = calculator
try:
    energy_ev = atoms.get_potential_energy()
    forces_ev_per_angstrom = atoms.get_forces()
    charges_e = atoms.get_charges()
finally:
    calculator.close()
```

Use `backend="cuda"` to require CUDA. Use `backend="auto"` only when CPU fallback is acceptable.

## ASE Optimization or Dynamics

```python
from ase.build import molecule
from ase.optimize import BFGS
from xtbloom.ase import XTBloom

atoms = molecule("H2O")
calculator = XTBloom(
    method="GFN2-xTB",
    backend="cuda",
    charge=0,
    multiplicity=1,
    warm_start=True,
)
atoms.calc = calculator
try:
    optimizer = BFGS(atoms, trajectory="h2o.traj")
    optimizer.run(fmax=0.05)  # eV/angstrom, the ASE convention.
finally:
    calculator.close()
```

ASE owns the optimizer and trajectory. xTBloom supplies repeated energies and analytic forces. The same ownership boundary applies to ASE molecular dynamics.

## dpdata Labeling

```python
import dpdata
import xtbloom.dpdata  # Ensure the plugin module is loaded.

system = dpdata.System("geometry.xyz", fmt="xyz")
labeled = system.predict(
    driver="xtbloom",
    backend="cuda",
    charge=0,
    multiplicity=1,
)

energies_ev = labeled.data["energies"]
forces_ev_per_angstrom = labeled.data["forces"]
```

For per-frame charge or spin, keep the corresponding values in the dpdata data dictionary and omit the fixed driver argument. Verify the concrete dpdata version's public accessor if it differs from `.data`.

An explicit driver is useful when sharing configuration:

```python
from xtbloom.dpdata import XTBloomDriver

driver = XTBloomDriver(
    backend="cpu",
    charge=0,
    multiplicity=1,
    max_scc_iterations=300,
)
labeled = driver.label(system.data)
```

`driver.label()` returns a data dictionary. `system.predict(...)` returns the container type defined by dpdata.

## dpdata Batch Relaxation

```python
import dpdata
from xtbloom.dpdata import XTBloomDriver

system = dpdata.System("geometries.xyz", fmt="xyz")
relaxed = system.minimize(
    minimizer="xtbloom",
    driver=XTBloomDriver(
        backend="cuda",
        charge=0,
        multiplicity=1,
    ),
    fmax=5e-3,  # eV/angstrom.
    max_steps=1000,
)
```

This relaxation is the dpdata adapter's batch L-BFGS loop over repeated single-point calls. It is not a native xTBloom optimization API.

## Reject Periodic Inputs Up Front

For ASE:

```python
if atoms.pbc.any():
    raise ValueError("xTBloom's ASE calculator accepts molecular inputs only")
```

For dpdata, require the system's `nopbc` data to be true for every frame. Do not clear periodic metadata merely to bypass validation; obtain an explicitly isolated molecular structure from the user instead.
