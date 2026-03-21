# PBC and input-type decisions

This reference helps decide:

- which input type to use
- whether to rely on embedded cell information
- when to use `--cell`
- when to use `--nopbc`

## Input-type mapping

### `dump`

Use for LAMMPS dump / lammpstrj trajectories, especially when the file contains `ITEM:` blocks such as:

- `ITEM: TIMESTEP`
- `ITEM: NUMBER OF ATOMS`
- `ITEM: BOX BOUNDS`
- `ITEM: ATOMS`

### `bond`

Use for bond-trajectory style inputs such as `bonds.reaxc`.

### `xyz`

Use for plain XYZ files without embedded extended metadata.

### `extxyz`

Use when the XYZ file explicitly carries extended metadata / cell information in extended XYZ format.

## PBC rules

### LAMMPS dump with valid `BOX BOUNDS`

Default behavior:

- treat as periodic unless there is a strong reason not to
- do **not** ask the user for `--cell`
- do **not** add `--nopbc` by default

### XYZ / extxyz with cell information available

- if the chosen path uses native `reacnetgenerator` and cell information is not already handled by the format itself, pass `--cell`
- avoid redundant manual cell input when the format/toolchain already carries valid cell metadata

### XYZ without cell information

Ask the user only if needed:

- Is this trajectory periodic?
- If periodic, what is the 3x3 cell matrix?
- If non-periodic or unknown, should the run use `--nopbc`?

### When `--nopbc` is appropriate

Use `--nopbc` when:

- the system is genuinely non-periodic
- the trajectory has already been unwrapped / reconstructed and periodic reconstruction is not desired
- no meaningful cell information exists and non-periodic treatment matches the user’s intent

### When `--nopbc` is usually wrong

Avoid `--nopbc` when:

- a standard periodic MD box is present in the trajectory
- the user has not asked for non-periodic treatment
- the only reason is “to make the command shorter”

## Wrapper vs native CLI

### Prefer wrapper (`rng-pipeline`) when

- input is a standard LAMMPS dump workflow
- atom names may need inference from `.data`
- you want predictable output layout
- you do not need official low-level flags beyond the wrapper surface

### Prefer native CLI when

- you need `--cell`
- you need `--nopbc`
- you need ASE bond detection controls
- you need custom HMM matrices
- you need `--miso`, `--selectatoms`, or `--nproc`

## LAMMPS coordinate note

For standard LAMMPS dump workflows, coordinate representation matters:

- if the dump already contains `x y z`, no conversion is needed
- if the dump contains scaled coordinates such as `xs ys zs`, use the wrapper path or a preprocessing path that converts them correctly before analysis
- if conversion or triclinic handling is ambiguous, stop and inspect rather than guessing
