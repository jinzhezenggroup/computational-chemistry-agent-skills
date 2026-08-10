# High-Level Python Inference

Use this reference for `Calculator`, `Structure`, and `BatchCalculator`. It is self-contained for an installed skill; verify the online API guide when working with a different xTBloom release.

## Public Contract

xTBloom's high-level Python interface uses NumPy host arrays and the same native C ABI on CPU and CUDA.

| Quantity                 | Unit or meaning                     |
| ------------------------ | ----------------------------------- |
| Atomic positions         | bohr                                |
| Energy                   | Hartree                             |
| Forces                   | Hartree/bohr and equal to `-dE/dR`  |
| `result["gradient"]`     | `-result["forces"]`                 |
| Atomic charge            | elementary-charge units             |
| `electronic_temperature` | kelvin in the high-level Python API |

At finite electronic temperature, the reported variational energy is the electronic Helmholtz free energy.

`backend="cpu"` and `backend="cuda"` require that backend. `backend="auto"` prefers CUDA but can fall back to CPU. Use an explicit backend whenever execution on that backend is part of the requirement.

## Single-System Example

The coordinates below are in bohr. Keep the context alive when updating geometry so its workers, plans, workspaces, and optionally its compatible electronic state can be reused.

```python
import numpy as np
from xtbloom import Calculator

numbers = np.array([8, 1, 1], dtype=np.int32)
positions_bohr = np.array(
    [
        [0.0000000000, 0.0000000000, -0.7357858611],
        [1.4418315287, 0.0000000000, 0.3678929305],
        [-1.4418315287, 0.0000000000, 0.3678929305],
    ],
    dtype=np.float64,
)

with Calculator(
    "GFN2-xTB",
    numbers,
    positions_bohr,
    backend="cpu",  # Change to "cuda" only when CUDA is required.
    electronic_temperature=300.0,  # kelvin
) as calculator:
    result = calculator.singlepoint()

print(f"energy = {result.energy:.16g} Hartree")
print("forces [Hartree/bohr]:")
print(result.forces)
print("charges [e]:")
print(result.charges)
```

`Calculator.singlepoint()` raises if its one system fails SCC convergence or eigensolution. Preserve the exception and native diagnostic rather than treating missing results as zeros.

## Repeated Geometry Updates and Warm Starts

The default `warm_start=False` gives each call an independent fresh SCC solve. To seed each compatible geometry from the preceding converged electronic state:

```python
with Calculator(
    "GFN2-xTB",
    numbers,
    positions_bohr,
    backend="cpu",
    warm_start=True,
) as calculator:
    first = calculator.singlepoint()
    calculator.update(positions=positions_bohr * 1.01)
    second = calculator.singlepoint()
```

The high-level wrapper starts fresh on the first call and after an incompatible topology or compute-policy identity change. Warm start is an initial-guess policy, not permission to reuse a stale final result.

## Heterogeneous Ragged-Batch Example

Each `Structure` can have a different number of atoms, charge, and spin state. One `BatchCalculator.compute()` call preserves their input order.

```python
import numpy as np
from xtbloom import BatchCalculator, Structure

systems = [
    Structure(
        [1, 1],
        np.array([[-0.7, 0.0, 0.0], [0.7, 0.0, 0.0]], dtype=np.float64),
    ),
    Structure(
        [8, 1, 1],
        np.array(
            [
                [0.0000, 0.0000, -0.7358],
                [1.4418, 0.0000, 0.3679],
                [-1.4418, 0.0000, 0.3679],
            ],
            dtype=np.float64,
        ),
    ),
]

with BatchCalculator(
    systems,
    backend="cuda",  # Requires CUDA; use "cpu" for a CPU requirement.
    electronic_temperature=300.0,
) as calculator:
    batch = calculator.compute()

failed = {int(index) for index in batch.failed_indices}
for index in range(len(batch)):
    if index in failed:
        print(
            f"system {index} failed: status={batch.per_system_status[index]}, "
            f"converged={batch.scc_converged[index]}, "
            f"iterations={batch.scc_iterations[index]}"
        )
        continue
    system_result = batch[index]
    print(index, system_result.energy, system_result.forces)

# Raise after preserving or reporting successful peers when strict behavior is desired.
batch.raise_for_status()
```

A successful batch call means diagnostics were published; it does not mean every member succeeded. Failed systems have NaNs in every requested floating-point slice. Successful peer slices remain valid.

Passing `raise_on_failure=True` to `compute()` raises before returning the `BatchResult`. Prefer the default when the application needs successful peers even if another member fails.

## Large CUDA Batches

`compute(auto_batch_size=True)` chooses a conservative CUDA chunk size and retries recoverable multi-system allocation failures at smaller chunks. An integer supplies a target maximum total atom count per chunk. Systems remain indivisible and order is preserved.

Do not combine `auto_batch_size` with `warm_start=True`: one native context retains one whole-batch checkpoint, not a checkpoint for each chunk.

## Charge and Spin

`Structure(..., charge=<value>)` sets molecular charge. Use either `multiplicity` or `uhf = multiplicity - 1`; inconsistent values are errors. Open-shell systems default to two unrestricted spin channels. Set `spin_channels=1` only when the restricted open-shell formulation is intended.

Both restricted and unrestricted GFN2-xTB are implemented on CPU and CUDA.

## Scope Boundaries

This workflow does not cover direct device arrays, DLPack result ownership, PyTorch autograd, ASE/dpdata unit conversion, the native C API, or QM/MM force responsibilities. Use their dedicated integration guidance.

Do not generate examples that claim GFN1-xTB, ROCm, lattice/PBC inputs, solvation, native geometry optimization, molecular dynamics, Hessians, or higher-order autograd. xTBloom currently implements only GFN2-xTB; adapter-level minimizers are repeated single-point workflows, not native optimization support.

Authoritative online sources:

- <https://github.com/jinzhezenggroup/xtbloom/blob/main/docs/user-guide/python.md>
- <https://github.com/jinzhezenggroup/xtbloom/blob/main/docs/user-guide/index.md>
- <https://github.com/jinzhezenggroup/xtbloom/blob/main/python/README.md>
