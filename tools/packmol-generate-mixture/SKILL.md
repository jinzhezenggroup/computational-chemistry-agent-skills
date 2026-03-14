---
name: packmol-generate-mixture
description: Generate an initial packed molecular configuration (packed XYZ) from one or more single-molecule XYZ structures using Packmol. Use when you need to pack molecules into a cubic box for MD/prep; ask for packing parameters (counts, density/box, tolerance) and desired output location; then generate Packmol input, run Packmol via uvx, and report output paths + box metadata.
metadata:
  openclaw:
    emoji: "📦"
    requires:
      bins: ["uv", "python3"]
    os: ["linux", "darwin"]
---

# packmol-generate-mixture

Use Packmol to generate an initial **packed** configuration for a molecular mixture.

## Agent responsibilities (do these in order)

1. **Collect inputs** (ask if missing; do not guess):
   - component structure files (XYZ), one per species (e.g. `species1.xyz`, `species2.xyz`)
   - molecule counts for each species (e.g. `species1: 100`, `species2: 650`)
   - **either** target density (g/cm^3) **or** a fixed cubic box length (Å)
   - Packmol `tolerance` (Å)
   - **output location**: output directory + output filename prefix (system name)

2. **Validate inputs**:
   - confirm XYZ files exist and are readable
   - confirm the first line (atom count) matches the number of coordinate lines
   - if density-based box estimation is requested: confirm each molecule’s elemental composition can be inferred from the XYZ symbols

3. **Decide box size**:
   - If user provides `box_length_A`: use it.
   - Else compute `box_length_A` from density (see formula below).

4. **Create a working folder** at the requested output location:
   - copy the component XYZ files into it (or reference them with absolute paths)

5. **Write Packmol input** `${system_name}.inp`:
   - one `structure ... end structure` block per component
   - all components share the same `inside box 0 0 0 L L L`

6. **Run Packmol locally**:
   - Prefer: `uvx packmol -i ${system_name}.inp`
   - If you need to force the source package: `uvx --from packmol packmol -i ${system_name}.inp`

7. **Report results**:
   - exact output paths (inp, xyz, log)
   - final box length (Å) and the parameters used (counts, density or fixed L, tolerance)
   - basic sanity checks (total molecules, total atoms)

8. **(Optional) Post-process for LAMMPS**

If the user plans to run LAMMPS (especially ReaxFF), they often need a LAMMPS data file with correct box bounds.

- If you convert XYZ -> LAMMPS data with dpdata, dpdata may write default box bounds (e.g., 0..100 Å).
- Fix the bounds to match the Packmol cubic box length using `lammps-md-tools` from PyPI:

```bash
uvx --from lammps-md-tools lammps-fix-box \
  --in  input.data \
  --out output.boxfix.data \
  --L 60.690 \
  --wrap
```

This rewrites `xlo/xhi`, `ylo/yhi`, `zlo/zhi` to `0..L`, zeroes tilt factors, and optionally wraps atoms into the box.

## What to ask the user (plain language)

If the user didn’t specify them, ask **at minimum**:

- **Packing counts**: how many molecules of each species? (e.g., `species1=100, species2=650`)
- **Box definition**: do you want to estimate a cubic box from a target density (g/cm^3), or do you want to provide a fixed cubic box length L (Å)?
- **Tolerance**: what Packmol `tolerance` (Å) should be used? (common starting point: 2.0 Å)
- **Output location**: which directory should receive the results, and what system name / filename prefix should be used?

If the user says “use defaults”, propose defaults:
- `tolerance = 2.0 Å`
- output dir: a `packed/` subfolder under the folder containing the input XYZ
- (density) **do not assume**; ask for it, but you may suggest a starting value the user can confirm.

## Input schema (recommended)

Example (replace with your own species/files):

```yaml
system_name: mixture_pack
output_dir: /path/to/output/packed
# Choose ONE of the following:
density_g_cm3: 0.25
# box_length_A: 60.69

tolerance_A: 2.0
components:
  - name: species1
    structure_file: /path/to/species1.xyz
    number: 100
  - name: species2
    structure_file: /path/to/species2.xyz
    number: 650
```

## Density → cubic box length (Å)

When `density_g_cm3` is provided and `box_length_A` is not, estimate L from total mass:

- infer each molecule’s elemental composition from its XYZ symbols
- use standard atomic masses (g/mol)
- compute total molar mass of the whole configuration (g/mol)
- convert to mass per configuration: `m_cfg = M_total / N_A` (g)
- compute volume in cm^3: `V_cm3 = m_cfg / density_g_cm3`
- convert to Å^3: `V_A3 = V_cm3 * 1e24`
- cubic length: `L_A = V_A3 ** (1/3)`

This is an **initial packing estimate** (geometry construction), not an equilibrated density.

## Output contract

The run should produce (within `output_dir`):
- `${system_name}.inp` (Packmol input)
- `${system_name}.xyz` (packed XYZ output; name may include `_packed` suffix)
- `packmol.out` (stdout log; capture with `tee`)

## Limitations (be explicit)

- Packed XYZ has coordinates only; **no topology**, **no force-field types**, **no LAMMPS data**.
- Packing success ≠ physically valid structure; minimization/equilibration still required.
