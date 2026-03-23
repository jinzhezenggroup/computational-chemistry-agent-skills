# ReacNetGenerator command recipes

Use these examples as templates. Prefer explicit paths and non-interactive execution.

## 1. Standard dump workflow via wrapper

```bash
uvx --refresh --from reacnet-md-tools rng-pipeline \
  --input /path/to/trajectory.lammpstrj \
  --type dump \
  --outroot out \
  --data /path/to/system.data \
  --nohmm \
  --stepinterval 10 \
  --maxspecies 50
```

Use this first for normal LAMMPS dump workflows.

## 2. Wrapper with interactive data-file selection

TTY only:

```bash
uvx --refresh --from reacnet-md-tools rng-pipeline \
  --input /path/to/trajectory.lammpstrj \
  --type dump \
  --outroot out \
  --pick-data
```

## 3. Native CLI for bond trajectory

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type bond \
  -i /path/to/bonds.reaxc \
  -a C H O \
  --nohmm
```

## 4. Native CLI for XYZ with explicit cell

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type xyz \
  -i /path/to/md.xyz \
  -a C H O \
  --nohmm \
  --cell 10 0 0 0 10 0 0 0 10
```

## 5. Native CLI for non-periodic XYZ

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type xyz \
  -i /path/to/md.xyz \
  -a C H O \
  --nohmm \
  --nopbc
```

## 6. Native CLI with selective graph elements

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type dump \
  -i /path/to/dump.reaxc \
  -a C H O Cl \
  --nohmm \
  --selectatoms C O
```

## 7. Native CLI with isomer merging

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type dump \
  -i /path/to/dump.reaxc \
  -a C H O \
  --miso 1
```

## 8. Inspect existing outputs with `rng-query`

```bash
uvx --refresh --from reacnet-md-tools rng-query species \
  --reac out/run/run.reactionabcd \
  --formula C6H6
```

Other common query modes:

```bash
uvx --refresh --from reacnet-md-tools rng-query next \
  --reac out/run/run.reactionabcd \
  --smiles '[CH3][CH3]'

uvx --refresh --from reacnet-md-tools rng-query rxn-formula \
  --reac out/run/run.reactionabcd \
  --reactants C6H6 \
  --products C6H5+H
```

## 9. Launch local browser UI

Only when the user explicitly wants it:

```bash
uvx --refresh --from reacnet-md-tools rng-webapp \
  --reac out/run/run.reactionabcd \
  --host 127.0.0.1 \
  --port 8000
```

## Recipe-selection hints

- If the user says “just run it” and provides a LAMMPS dump: use recipe 1.
- If the user asks for `--cell`, `--nopbc`, ASE cutoffs, or HMM matrices: switch to native CLI recipes.
- If the user already has `.reactionabcd` / `.species`: use recipe 8, not a rerun.
