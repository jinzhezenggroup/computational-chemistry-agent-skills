# Commands and Workflow

Use this reference for backend-agnostic phonopy workflows.

## Role split

- This skill owns `phonopy` orchestration.
- Backend skills (VASP/QE/MLFF) own force calculations for displaced supercells.

## Recommended task layout

`structure.ext` is a placeholder filename. Replace it with your real structure file,
for example `POSCAR`, `structure.cif`, or `structure.xyz` (with cell information
provided consistently for periodic systems).

```text
phonopy_task/
├── input/
│   └── structure.ext
├── displacements/
├── backend-forces/
├── FORCE_SETS (or force_constants.hdf5)
└── output/
```

## Core command patterns

### 1) Generate displacements

```bash
phonopy -d --dim="2 2 2" -c input/structure.ext
```

Optional amplitude control:

```bash
phonopy -d --dim="2 2 2" --amplitude=0.01 -c input/structure.ext
```

### 2) Build force dataset

Use backend forces for each displaced supercell and assemble `FORCE_SETS` according to phonopy format.

### 3) Run mesh / DOS / thermal properties

```bash
phonopy --mesh="20 20 20" -t --dos -c input/structure.ext
```

### 4) Run band structure

```bash
phonopy-load --band="0 0 0  0.5 0 0  0.5 0.5 0  0 0 0" --band-points=101
```

## Backend notes

### VASP backend

- run force calculations on each displaced supercell
- parse forces and assemble phonopy-compatible dataset

### QE backend

- run force calculations for displaced structures
- ensure consistent units and force convention before assembly

### MLFF backend (e.g., DeePMD/LAMMPS)

- evaluate forces for all displaced supercells with identical model/version
- verify model applicability before trusting imaginary-mode behavior

## Quality checklist

1. displacement count matches force-file count
1. force units are consistent
1. supercell size is convergence-checked
1. path/mesh settings are documented in output summary
