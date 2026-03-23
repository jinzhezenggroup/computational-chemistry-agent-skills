# Commands and Workflow

Use this reference when the user wants a concrete, file-oriented `dft-vasp` workflow.

## Recommended task layout

Prefer a compact task directory:

```text
vasp_task/
├── POSCAR
├── INCAR
├── KPOINTS   (optional)
└── POTCAR    (or assembly instructions)
```

## Workflow

1. Read user-provided structure.
1. Normalize to `POSCAR` if needed.
1. Confirm task type (`static` or `relax`).
1. Collect required parameters.
1. Generate `INCAR` with `KSPACING` by default.
1. Generate `KPOINTS` only if user asks for explicit manual mesh.
1. Return file set and POTCAR assembly instructions.

## Parameter checklist

### Must provide

- `ENCUT`
- k-point policy (`KSPACING` preferred for v0.1)
- `ISMEAR` / `SIGMA`
- POTCAR mapping for each element

### Usually should be explicit

- `EDIFF`
- `NELM`
- `PREC`
- `LREAL`
- `ISPIN` / `MAGMOM` if relevant
- `IVDW` if relevant

### Relax-only

- `IBRION`
- `NSW`
- `EDIFFG`
- `ISIF` (must match intended relaxation target)

## Minimal INCAR examples

### static (KSPACING-based)

```text
SYSTEM = example-static
ENCUT = 520
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
NELM = 120
ISPIN = 1
KSPACING = 0.20
```

### relax (illustrative)

```text
SYSTEM = example-relax
ENCUT = 520
EDIFF = 1E-6
EDIFFG = -0.02
IBRION = 2
NSW = 120
ISMEAR = 0
SIGMA = 0.05
ISIF = 2
KSPACING = 0.20
```

## Optional explicit KPOINTS example

Generate only when user explicitly requests manual mesh:

```text
Automatic mesh
0
Gamma
4 4 4
0 0 0
```

## POTCAR assembly note

This skill should provide explicit mapping and ordering, for example:

- `Si -> Si`
- `O -> O`

`POTCAR` must be assembled in the exact species order listed in `POSCAR`.
For example, if `POSCAR` species line is `Si O`, assemble:

- `POTCAR(Si)` then `POTCAR(O)`

Example command pattern (adapt paths to your local pseudopotential library):

```bash
cat /path/to/potpaw_PBE/Si/POTCAR /path/to/potpaw_PBE/O/POTCAR > POTCAR
```

## Next-stage execution (outside this skill)

```bash
vasp_std > vasp.out
```

or with scheduler launcher:

```bash
srun vasp_std > vasp.out
```

Execution/submission should be handled by `dpdisp-submit`.
