# ReaxFF workflow notes

This note is intentionally short and practical.

## Core pieces for a working ReaxFF MD in LAMMPS

1. **Charge support**
   - Use a charge-capable atom style, such as `atom_style charge` or `atom_style full`; per-atom charges are then read from the data file or initialized/updated by the charge-equilibration (QEq) fix.

2. **ReaxFF pair style**
   - Typical minimal form:
     ```lammps
     pair_style reaxff NULL
     pair_coeff * * ffield.reax <elem1> <elem2> ...
     ```
   - The element list defines the mapping from LAMMPS atom types (1..Ntypes) to element symbols.

3. **Charge equilibration (QEq)**
   - Most ReaxFF parameterizations expect QEq each step:
     ```lammps
     fix fqeq all qeq/reaxff 1 0.0 10.0 1.0e-6 reaxff
     ```
   - If you disable it (`pair_style reaxff ... checkqeq no`), you are running with fixed charges; this is unusual and should be explicit.

## Species analysis

To track reaction products, use `fix reaxff/species`:

```lammps
fix fspecies all reaxff/species 10 10 100 species.out
```

- Tune bond-order cutoffs via `cutoff` keyword if species are fragmented or over-bonded.

## Common failure modes

- **"Unknown pair_style reaxff"** → LAMMPS not built with REAXFF package.
- **Missing QEq fix warning/error** → add `fix qeq/reaxff ...` or explicitly disable check via `checkqeq no` (not recommended unless you know what you're doing).
- **QEq not converging** → adjust tolerance/maxiter or improve initial charges; also ensure the system is not too small relative to cutoffs.

## Links

- pair_style reaxff: https://docs.lammps.org/pair_reaxff.html
- fix qeq/reaxff: https://docs.lammps.org/fix_qeq_reaxff.html
- fix reaxff/species: https://docs.lammps.org/fix_reaxff_species.html
