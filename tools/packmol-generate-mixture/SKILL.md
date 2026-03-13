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
   - component structure files (XYZ), one per species (e.g. `2CP_opt.xyz`, `O2_opt.xyz`)
   - molecule counts for each species (e.g. `2CP: 100`, `O2: 650`)
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

## What to ask the user (plain language)

If the user didn’t specify them, ask **at minimum**:

- **打包参数**：每种分子各放多少个？（例如 2CP=100, O2=650）
- **盒子/密度**：你希望用目标密度 (g/cm³) 来估算盒子，还是直接给定立方盒边长 L (Å)？
- **tolerance**：最小分子间距 tolerance (Å) 用多少？（常见 2.0 Å）
- **输出位置**：结果写到哪个目录？系统名/文件前缀叫啥？（例如输出到 `.../packed/`，文件前缀 `2CP_O2_1ER`）

If the user says “用默认值”, propose defaults:
- `tolerance = 2.0 Å`
- output dir: a `packed/` subfolder under the folder containing the input XYZ
- (density) **do not assume**; ask for it, but you may suggest a starting value the user can confirm.

## Input schema (recommended)

```yaml
system_name: 2CP_O2_1ER
output_dir: /home/vlab/2CP_O2_1ER/packed
# Choose ONE of the following:
density_g_cm3: 0.25
# box_length_A: 60.69

tolerance_A: 2.0
components:
  - name: 2CP
    structure_file: /home/vlab/2CP_O2_1ER/2CP_opt.xyz
    number: 100
  - name: O2
    structure_file: /home/vlab/2CP_O2_1ER/O2_opt.xyz
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
