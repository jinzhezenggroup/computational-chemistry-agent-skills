---
name: xtbloom-run-python-inference
description: Write, review, and run high-level xTBloom Python GFN2-xTB inference with `Calculator`, `Structure`, and `BatchCalculator`, including single systems, repeated geometry updates, heterogeneous ragged batches, backend selection, units, finite-temperature meaning, and peer-local failure handling. Use for ordinary NumPy-based energy, force, and charge workflows; use a dedicated integration skill instead for Array API/DLPack/PyTorch zero-copy, ASE/dpdata, the native C API, or QM/MM coupling.
---

# Run xTBloom Python Inference

Build a calculation whose units, backend behavior, lifetime, and failure policy are explicit. Read [references/python-inference.md](references/python-inference.md) for the public API contract and complete examples.

## Run Standalone Programs Ephemerally

Do not require xTBloom to be preinstalled for an agent-generated standalone
program. Add PEP 723 metadata at the top, then run it with `uv run --script calculation.py`:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["xtbloom>=0.1.1"]
# ///
```

Respect an existing application environment when the user asks to modify one;
do not replace its dependency policy merely to make the example standalone.

## Select the Interface

- Use `Calculator` for one system and for repeated geometry updates on one topology.
- Use `Structure` plus `BatchCalculator` for differently sized systems in one native ragged request.
- Use context managers so native contexts and persistent backend resources are released deterministically.
- Keep this workflow on high-level NumPy-backed inputs. Route direct device arrays, caller-owned outputs, DLPack, and PyTorch autograd to the zero-copy integration workflow.
- Route ASE/dpdata unit conversion and adapter behavior, native C/C++ consumers, and QM/MM external operators to their dedicated workflows.

## Make Backend Intent Explicit

Choose `backend="cpu"` or `backend="cuda"` when that backend must execute. Choose `"auto"` only when preferring CUDA with CPU fallback is acceptable. Never infer a CUDA pass from an `auto` calculation without confirming the resolved backend; for a GPU acceptance check, require `"cuda"` and let an unavailable runtime fail clearly.

If import, native-library loading, CPU provider creation, or CUDA context creation fails, diagnose the installation before changing the scientific request.

## Preserve Numerical Meaning

Always state the following alongside generated input and output code:

| Quantity                 | High-level Python unit or meaning |
| ------------------------ | --------------------------------- |
| Positions                | bohr                              |
| Energy                   | Hartree                           |
| Forces                   | Hartree/bohr                      |
| `gradient`               | `-forces`                         |
| Charges                  | elementary-charge units           |
| `electronic_temperature` | kelvin                            |

At finite electronic temperature, the reported variational energy is the electronic Helmholtz free energy. Do not label input coordinates as angstrom unless they were converted to bohr before constructing the high-level xTBloom object.

## Handle Results Honestly

`Calculator.singlepoint()` raises when its single system does not converge or its eigensolver fails. `BatchCalculator.compute()` instead preserves peer-local results by default:

1. Inspect `failed_indices`, `per_system_status`, `scc_converged`, and `scc_iterations`.
1. Use successful peer results normally.
1. Treat every requested floating-point slice for a failed system as invalid NaN output.
1. Call `result.raise_for_status()` after inspection when strict exception behavior is desired, or pass `raise_on_failure=True` only when losing direct access to the returned peer results is acceptable.

A successful batch function return does not mean every member converged.

## Reuse State Deliberately

The default `warm_start=False` makes each high-level calculation an independent fresh SCC solve. For iterative geometry work, reuse one `Calculator`, call `update(positions=...)`, and enable `warm_start=True` only when seeding from the previous compatible converged state is intended. The high-level wrapper transparently starts fresh on the first call or after an incompatible identity change.

For large CUDA batches, `auto_batch_size=True` may split and retry recoverable allocation failures while preserving order and peer diagnostics. Do not combine automatic slicing with `warm_start=True`, because one native context owns one whole-batch checkpoint.

## Keep Scope Accurate

Use only `GFN2-xTB`. Restricted and unrestricted calculations are supported on CPU and CUDA; specify `multiplicity` or `uhf = multiplicity - 1` consistently for open-shell systems. Do not claim support for GFN1-xTB, ROCm, lattice/PBC inputs, solvation, native geometry optimization, molecular dynamics, Hessians, or higher-order autograd.

Report the requested and resolved backend, input units, temperature, batch failure summary, and any unavailable runtime. Do not turn CPU fallback or an unexecuted backend into a pass.
