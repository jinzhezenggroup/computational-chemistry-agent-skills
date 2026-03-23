# Commands and Workflow

Use this reference when the user asks for concrete, file-oriented `pymatgen-structure` operations.

## Recommended task layout

Use a small task directory such as:

```text
pymatgen_task/
├── input/
│   └── structure.cif
├── output/
└── notes.txt
```

## Environment setup (recommended)

Run pymatgen with `uv` so the environment is explicit:

```bash
uv run --with pymatgen python -c "import pymatgen; print(pymatgen.__version__)"
```

## Workflow

1. Read and validate the input structure.
1. Confirm the operation type and required parameters.
1. Execute the operation.
1. Write output file(s).
1. Report changed composition, atom count, and key analysis values.

## Command patterns

### 1) Format conversion (`cif` -> `POSCAR`)

```bash
uv run --with pymatgen python - <<'PY'
from pymatgen.core import Structure
s = Structure.from_file("input/structure.cif")
s.to(filename="output/POSCAR")
print("wrote output/POSCAR")
PY
```

### 2) Build a 2x2x1 supercell

```bash
uv run --with pymatgen python - <<'PY'
from pymatgen.core import Structure
s = Structure.from_file("input/structure.cif")
s.make_supercell([[2, 0, 0], [0, 2, 0], [0, 0, 1]])
s.to(filename="output/supercell.cif")
print("sites:", len(s))
print("formula:", s.composition.reduced_formula)
PY
```

### 3) Species substitution (all Si -> Ge)

```bash
uv run --with pymatgen python - <<'PY'
from pymatgen.core import Structure
s = Structure.from_file("input/structure.cif")
s.replace_species({"Si": "Ge"})
s.to(filename="output/substituted.cif")
print("formula:", s.composition.formula)
PY
```

### 4) Symmetry analysis (space group)

```bash
uv run --with pymatgen python - <<'PY'
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

s = Structure.from_file("input/structure.cif")
spg = SpacegroupAnalyzer(s, symprec=1e-3)
print("space_group_symbol:", spg.get_space_group_symbol())
print("space_group_number:", spg.get_space_group_number())
PY
```

### 5) Neighbor distance summary around one site

```bash
uv run --with pymatgen python - <<'PY'
from pymatgen.core import Structure

s = Structure.from_file("input/structure.cif")
site_index = 0
neighbors = s.get_neighbors(s[site_index], r=3.0)
print("site", site_index, "neighbor_count", len(neighbors))
for n in sorted(neighbors, key=lambda x: x.nn_distance)[:10]:
    print(n.specie, round(n.nn_distance, 4))
PY
```

## Notes and guardrails

- If periodic workflow is requested but input is plain xyz without cell, ask for cell data.
- For random doping workflows, request explicit random seed and substitution fraction.
- Keep a record of parameters used (`symprec`, cutoff radius, scaling matrix) in final report.
- This skill prepares structures and analysis only. Submission/execution should be handled by a separate workflow skill.
