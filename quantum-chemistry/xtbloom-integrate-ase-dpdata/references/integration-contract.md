# ASE and dpdata Integration Contract

## Scope

xTBloom implements molecular GFN1/GFN2-xTB single-point inference. The ASE and dpdata integrations adapt that inference to their host frameworks. GFN1-xTB is CPU-only; GFN2-xTB supports CPU and CUDA. The adapters do not add periodic execution or native xTBloom optimization and dynamics APIs.

Solvation, lattice/PBC calculations, Hessians, and native molecular dynamics are outside this contract.

## Units at the Adapter Boundaries

| Quantity                        | ASE               | dpdata                      | Native xTBloom underneath       |
| ------------------------------- | ----------------- | --------------------------- | ------------------------------- |
| Coordinates                     | angstrom          | angstrom                    | bohr                            |
| Energy                          | eV                | eV                          | Hartree                         |
| Forces                          | eV/angstrom       | eV/angstrom                 | Hartree/bohr                    |
| Charges                         | elementary charge | not published by the driver | elementary charge               |
| Electronic temperature argument | kelvin            | kelvin                      | converted to `k_B T` in Hartree |

The adapters perform the coordinate, energy, and force conversions. User code must not convert those values a second time.

At finite electronic temperature, the variational energy is the electronic Helmholtz free energy even though ASE exposes it through both `energy` and `free_energy`.

## ASE Calculator

Import the calculator as:

```python
from xtbloom.ase import XTBloom
```

It implements these ASE properties:

- `energy` and the identical `free_energy`, in eV;
- `forces`, in eV/angstrom;
- `charges`, in elementary-charge units.

Important constructor settings and defaults:

| Setting                  | Default      | Meaning                                                                             |
| ------------------------ | ------------ | ----------------------------------------------------------------------------------- |
| `method`                 | `"GFN2-xTB"` | `"GFN1-xTB"` or `"GFN2-xTB"`                                                        |
| `charge`                 | `None`       | Sum `atoms.get_initial_charges()` when omitted                                      |
| `multiplicity`           | `None`       | Derive unpaired electrons from rounded sum of initial magnetic moments when omitted |
| `electronic_temperature` | `300.0`      | kelvin                                                                              |
| `max_scc_iterations`     | `250`        | SCC iteration ceiling                                                               |
| `charge_tolerance`       | `1e-6`       | charge tolerance                                                                    |
| `energy_tolerance`       | `1e-8`       | Hartree                                                                             |
| `backend`                | `"auto"`     | prefer CUDA for GFN2; use CPU for GFN1                                              |
| `device_id`              | `None`       | selected CUDA device                                                                |
| `cpu_threads`            | `1`          | CPU batch-parallel worker ceiling                                                   |
| `cache_api`              | `True`       | retain the underlying xTBloom calculator                                            |
| `warm_start`             | `True`       | reuse the previous compatible converged electronic state as the SCC guess           |

Any true value in `atoms.pbc` raises an ASE input error. xTBloom must not reinterpret the cell as an isolated cluster silently.

With `cache_api=True`, coordinate updates reuse the native context. A species change rebuilds the fixed-topology calculator. `close()` releases the cached native calculator explicitly.

### Warm starts

ASE defaults to `warm_start=True` because optimizers and dynamics normally evaluate a related geometry sequence. Compatible steps seed SCC from the most recent converged electronic state. A first call or an incompatible request identity transparently uses a fresh solve through the high-level adapter.

Set `warm_start=False` when independent calculations must not depend on the order in which geometries were evaluated. Do not claim bitwise-independent calls while warm start is enabled.

Changing the geometry is compatible with reuse. Changing species, backend, device, worker configuration, or other identity-bearing policy can rebuild or invalidate the reusable state.

## dpdata Driver

The package registers both a driver and minimizer under the key `"xtbloom"`. Importing `xtbloom.dpdata` explicitly is a robust way to make the classes available when plugin discovery is not guaranteed.

`XTBloomDriver` labels every frame of one molecular `dpdata.System` through a native ragged-batch call. It returns:

- `energies` with shape `(nframes,)` in eV;
- `forces` with shape `(nframes, natoms, 3)` in eV/angstrom.

The driver is strict: if any frame fails SCC or the eigensolver, labeling raises instead of returning a mixture containing silent NaN labels.

Charge and spin are resolved per frame as follows:

1. A fixed constructor `charge` applies to every frame.
1. Otherwise use a per-frame `data["charge"]` value when present, then default to zero.
1. A fixed constructor `uhf` applies to every frame.
1. Otherwise a fixed `multiplicity` is interpreted as `uhf = multiplicity - 1`.
1. Otherwise use per-frame `data["uhf"]` or `data["multiplicity"]`; if neither exists, default to closed-shell `uhf=0`.

Do not supply inconsistent `uhf` and `multiplicity`. Open-shell calculations default to unrestricted spin channels unless `spin_channels=1` deliberately requests restricted open-shell behavior.

The driver forwards backend and SCC settings to `BatchCalculator`, including `backend`, `device_id`, `cpu_threads`, iteration/tolerance settings, and electronic temperature. A driver labeling call creates and closes its batch calculator around that call; do not expect it to retain a warm checkpoint across separate `predict()` calls.

A dpdata object is periodic when its `nopbc` data is false. The driver and minimizer reject it because xTBloom has no lattice input.

## dpdata Batch Minimizer

`XTBloomMinimizer` is an upper-level L-BFGS adapter. It is not native geometry optimization in the xTBloom C ABI.

Its main settings are:

| Setting     | Default                                        | Meaning                                                             |
| ----------- | ---------------------------------------------- | ------------------------------------------------------------------- |
| `driver`    | a new `XTBloomDriver()` using `backend="auto"` | method, charge/spin, backend, and SCC configuration                 |
| `fmax`      | `5e-3`                                         | convergence threshold in eV/angstrom                                |
| `max_steps` | `None`                                         | geometry moves after the initial evaluation; unlimited when omitted |
| `memory`    | `5`                                            | L-BFGS history pairs per frame                                      |

The minimizer moves all active frames in lockstep and evaluates them in one ragged batch per step. Converged frames are frozen and removed, so the active batch shrinks. When the active frame set changes, the adapter may rebuild its `BatchCalculator`; do not promise uninterrupted native warm-state reuse across the whole relaxation.

Only energy-accepted geometries become publishable results. If `max_steps` is reached, each frame is returned at its last accepted geometry, not an unevaluated or rejected trial.

The operation raises if a frame fails SCC/eigensolution or its line search stalls at the minimum step. This all-or-error boundary prevents failed frames from appearing as valid optimized structures.

The minimizer does not make periodic systems valid and does not expose the full ASE optimizer/constraint ecosystem. Use an ASE optimizer with `xtbloom.ase.XTBloom` when that ecosystem is required.
