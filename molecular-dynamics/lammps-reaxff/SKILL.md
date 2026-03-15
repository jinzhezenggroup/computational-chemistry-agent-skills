---
name: lammps-reaxff
description: "Run reactive molecular dynamics simulations in LAMMPS with the ReaxFF potential, including preparing input scripts (pair_style reaxff + fix qeq/reaxff), mapping LAMMPS atom types to elements via pair_coeff, choosing ensembles (NVE/NVT/NPT), and adding common ReaxFF diagnostics such as species analysis. Use when the user wants LAMMPS+ReaxFF workflows or needs a working, annotated `input.lammps` template."
compatibility: "Requires a LAMMPS build with the REAXFF package enabled (pair_style reaxff and fix qeq/reaxff). Optional acceleration variants: reaxff/omp or reaxff/kk."
license: MIT
metadata:
  author: OpenClaw
  version: "1.0"
  repository: https://www.lammps.org/
  lammps_docs: https://docs.lammps.org/
---

# LAMMPS + ReaxFF

Use this skill when the user wants to run molecular dynamics in LAMMPS with a ReaxFF force field, prepare or explain an `input.lammps` file, and set up charge equilibration (QEq) correctly.

## Agent responsibilities

1. Confirm the **ReaxFF force field file** (e.g. `ffield.reax.*`). Do not guess which file is appropriate.
   - If the user does not have a force field yet, point them to known sources (e.g. LAMMPS `potentials/ffield.reax.*`, LAMMPS `examples/reaxff`, or the PSU Materials Computation Center / van Duin group repository).
2. Confirm the **structure/data file** (e.g. `data.system`) and the **atom type → element mapping** needed by `pair_coeff`.
3. Ensure the input includes charge handling:
   - Use an atom style that supports charges (commonly `atom_style charge`) **or** ensure charges exist via data file / `fix property/atom q`.
   - Add **one** charge equilibration fix, typically `fix qeq/reaxff`, unless the user explicitly requests otherwise.
4. Write the LAMMPS input script yourself; keep examples readable and annotated.
5. When possible, validate command availability against LAMMPS docs or local `lmp -h` output before execution.
6. Report clearly which command was run, which files were used, and where outputs were written.

## Minimum information to collect

Ask only for what is missing:

- LAMMPS data file path (or structure + how to generate a data file)
- ReaxFF force field file path (`ffield.reax...`)
- Atom types present and their element mapping (for `pair_coeff * * ffield ...`)
- Ensemble (NVE / NVT / NPT)
- Temperature, pressure (if NPT), timestep, run length
- Execution mode: online provisioning vs user-specified LAMMPS binary

## Execution mode

### Online mode (only if internet access + `uv` is available)

Use:

```bash
uvx --from lammps lmp -in input.lammps
```

Notes:
- This provisions a LAMMPS binary, but may not include the REAXFF package in all environments. If `pair_style reaxff` is missing, switch to offline mode.

### Offline mode (common / HPC)

Do **not** invent the executable. Ask which command should be used, e.g.:

- `lmp -in input.lammps`
- `mpirun -np 32 lmp_mpi -in input.lammps`
- `srun lmp -in input.lammps`

## Example: annotated NVT input (ReaxFF + QEq)

See also `assets/input.reaxff.nvt.lammps`.

```lammps
# --------- user knobs ---------
variable        NSTEPS      equal 200000
variable        THERMO      equal 200
variable        DUMP        equal 1000

variable        TEMP        equal 300.0
variable        TAU_T       equal 100.0

# Timestep (fs for units real). For high-T / reactive runs, 0.1 fs is often safer.
variable        DT          equal 0.25


# QEq parameters
variable        QEQ_EVERY   equal 1
variable        QEQ_TOL     equal 1.0e-6
variable        QEQ_CUTLO   equal 0.0
variable        QEQ_CUTHI   equal 10.0

units           real
boundary        p p p
atom_style      charge

read_data       data.system

neighbor        2.0 bin
neigh_modify    every 1 delay 0 check yes

# ReaxFF potential
pair_style      reaxff NULL
pair_coeff      * * ffield.reax C H O

# Charge equilibration (required for most ReaxFF parameterizations)
fix             fqeq all qeq/reaxff ${QEQ_EVERY} ${QEQ_CUTLO} ${QEQ_CUTHI} ${QEQ_TOL} reaxff
# (`reaxff` here means QEq parameters are extracted from the ReaxFF force field file.)

# Thermo and trajectory
thermo_style    custom step temp pe ke etotal press vol density
thermo          ${THERMO}

dump            1 all custom ${DUMP} traj.lammpstrj id type q x y z

# Dynamics
velocity        all create ${TEMP} 12345 mom yes rot yes dist gaussian
fix             fnvt all nvt temp ${TEMP} ${TEMP} ${TAU_T}

timestep        ${DT}
run             ${NSTEPS}
```

### Notes on the example

- `units real` is a common choice for ReaxFF (time in fs). Many published ReaxFF workflows use `real`, but the correct choice depends on the parameterization and your conventions.
- **Timestep**: `0.25 fs` may be fine for moderate temperatures, but for high-temperature ReaxFF (especially with H present) it is common to reduce to **`0.1 fs`** (or even `0.05 fs` if needed). A quick sanity check is a short NVE segment to verify total-energy drift before running long NVT/NPT.
- `atom_style charge` is used because ReaxFF and QEq require per-atom charges.
- `pair_style reaxff NULL` uses default ReaxFF control settings. If you have a ReaxFF control file, replace `NULL` with its filename.
- `pair_coeff * * ffield.reax C H O`:
  - The trailing symbols define the element mapping for LAMMPS atom types (type 1->C, type 2->H, type 3->O in this example). Adjust to match your data file.
- `fix qeq/reaxff ... reaxff` uses QEq parameters extracted from the ReaxFF force field file.

## Optional: species analysis

If the user wants reaction product tracking, add `fix reaxff/species` (see `references/reaxff-workflow.md`). This writes time series counts of detected molecular species using bond-order cutoffs.

## Output checklist

After a run, report at least:

- executed command
- input script path
- data file path
- ffield path and element mapping used
- whether QEq was enabled and with which settings
- main log path (`log.lammps`)
- trajectory/species output paths (if any)

## References

- pair_style reaxff: https://docs.lammps.org/pair_reaxff.html
- fix qeq/reaxff: https://docs.lammps.org/fix_qeq_reaxff.html
- fix reaxff/species: https://docs.lammps.org/fix_reaxff_species.html
