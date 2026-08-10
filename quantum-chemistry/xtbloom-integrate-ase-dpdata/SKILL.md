---
name: xtbloom-integrate-ase-dpdata
description: Integrate xTBloom with ASE or dpdata for molecular energy, force, charge, labeling, relaxation, optimizer, or dynamics workflows. Use when an AI coding agent needs to attach the xTBloom ASE calculator, configure dpdata's xtbloom driver or batch minimizer, preserve the adapters' eV/angstrom conventions, choose reproducible versus warm-started execution, or diagnose unsupported periodic inputs.
---

# Integrate xTBloom with ASE and dpdata

Use xTBloom's public adapters instead of duplicating their unit conversion, charge/spin resolution, batching, or failure handling. Keep the surrounding framework responsible for its workflow: ASE owns optimizers and dynamics, while dpdata owns dataset containers and invokes xTBloom's driver or minimizer plugin.

## Run Standalone Programs Ephemerally

For an agent-generated standalone program, add PEP 723 metadata and run it with
`uv run --script workflow.py`. Declare only the adapter being used:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["xtbloom[ase]>=0.1.1"]
# ///
```

Use `xtbloom[dpdata]>=0.1.1` instead for dpdata. Add `cuda12` to the same extra
list only when the selected Linux CUDA environment needs those user-space
libraries. Do not install ASE and dpdata together unless the program uses both.

## Load the Relevant References

- Read [integration-contract.md](references/integration-contract.md) before changing an ASE or dpdata integration. It is the self-contained behavioral contract.
- Read [recipes.md](references/recipes.md) when writing or reviewing executable user code.

## Choose the Integration Path

1. Use `xtbloom.ase.XTBloom` when the application already operates on `ase.Atoms`, uses an ASE optimizer or dynamics driver, or expects ASE properties.
1. Use dpdata's `driver="xtbloom"` or `XTBloomDriver` when labeling every frame of a molecular `dpdata.System` with energies and forces.
1. Use dpdata's `minimizer="xtbloom"` with `XTBloomDriver` when relaxing many molecular frames through the adapter's batch-native L-BFGS workflow.
1. Use xTBloom's lower-level Python interfaces instead when the task needs atomic-unit arrays, explicit point charges, charge-response operators, direct CUDA buffers, or per-system failure inspection not exposed by these adapters.

Do not route a periodic structure into either adapter. xTBloom has no lattice descriptor, and both integrations reject periodic inputs rather than treating them as isolated molecules.

## Gather the Scientific Intent

Before editing code, determine:

- whether the input is one molecule, an ASE trajectory, or a multi-frame dpdata system;
- the total charge and spin multiplicity, including whether they are fixed or vary per frame;
- whether CPU fallback is acceptable (`backend="auto"`) or the requested backend must be enforced (`"cpu"` or `"cuda"`);
- whether consecutive calls should share a compatible SCC starting state or remain independent and reproducible;
- whether the caller expects only single-point properties or a framework-owned optimization/dynamics workflow.

Never infer a nonzero charge, multiplicity, or periodic interpretation from geometry alone. Require the user or existing data model to provide scientifically meaningful values.

## Implement an ASE Workflow

1. Import `XTBloom` from `xtbloom.ase` and attach it to `atoms.calc`.
1. Pass `method="GFN2-xTB"` explicitly in generated examples. Only GFN2-xTB is implemented.
1. Set `backend` explicitly when silently changing backend would violate the request.
1. Set `charge` and `multiplicity` explicitly when known. Otherwise document ASE's fallback to initial charges and magnetic moments.
1. Choose `warm_start=True` for compatible geometry sequences such as optimization or dynamics. Choose `warm_start=False` for independent calls whose SCC initialization must not depend on an earlier step.
1. Let ASE consume and report positions in angstrom, energies in eV, and forces in eV/angstrom. Do not manually convert values around the adapter.
1. Close a long-lived calculator explicitly when the workflow ends so its native context and caches are released.

ASE optimizers and dynamics repeatedly call the calculator; they are not native xTBloom geometry optimization or molecular dynamics features. Preserve that distinction in code comments and user-facing explanations.

## Implement a dpdata Workflow

For labeling:

1. Select the registered `"xtbloom"` driver or construct `XTBloomDriver` when an explicit reusable configuration is clearer.
1. Pass fixed `charge`, `uhf`, or `multiplicity` only when those values apply to every frame. Otherwise preserve valid per-frame dpdata fields.
1. Treat driver failure as an error for the whole labeling operation. The adapter deliberately avoids publishing silent NaN labels when any frame fails SCC or the eigensolver.
1. Keep dpdata coordinates in angstrom and accept returned energies in eV and forces in eV/angstrom.

For relaxation:

1. Select `minimizer="xtbloom"` and pass a configured `XTBloomDriver` for backend and electronic settings.
1. Interpret `fmax` in eV/angstrom and `max_steps` as geometry moves after the initial force evaluation.
1. Explain that the minimizer is an upper-level, batch-native L-BFGS adapter built from repeated xTBloom single-point calls.
1. Preserve its all-or-error behavior for SCC/eigensolver failure or a stalled line search. Do not convert those failures into apparently valid relaxed structures.

Do not describe the dpdata minimizer as a native C-ABI optimizer, assume support for periodic cells, or imply that it implements arbitrary ASE constraints.

## Validate the Integration

Run the narrowest real workflow available and check all of the following:

- the input is explicitly molecular: `atoms.pbc` is false for ASE or dpdata marks the system nonperiodic;
- the requested backend is enforced when fallback is unacceptable;
- energy and force arrays are finite and have the expected framework shapes;
- reported units are eV and eV/angstrom at both adapter boundaries;
- charge and multiplicity reach the adapter through the intended fixed or per-frame path;
- a geometry update triggers a new calculation rather than reusing stale results;
- independent calculations use `warm_start=False`, while sequential workflows use warm start only intentionally;
- the calculator or driver-owned native resources are released when the host workflow ends.

When a requested feature lies outside these adapters, state the boundary and switch to the appropriate xTBloom interface instead of simulating unsupported behavior.
