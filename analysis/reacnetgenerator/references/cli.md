# ReacNetGenerator CLI reference

This file summarizes the **official ReacNetGenerator CLI** and maps it to agent usage.

Source used while preparing this reference:
- https://docs.deepmodeling.com/projects/reacnetgenerator/en/latest/guide/cli.html

## Official CLI shape

```bash
reacnetgenerator -i INPUT... -a ATOMNAME... [options]
```

Main official options:

- `-i`, `--inputfilename` — input trajectory file(s)
- `-a`, `--atomname` — atomic names, e.g. `C H O`
- `--nohmm` — disable HMM
- `--miso MISO` — merge isomers (`0`, `1`, `2`)
- `--dump` — deprecated; prefer `--type dump`
- `--type`, `-t` — one of:
  - `bond`
  - `lammpsbondfile`
  - `dump`
  - `lammpsdumpfile`
  - `xyz`
  - `extxyz`
- `--use-ase` — enable ASE-based bond detection
- `--ase-cutoff-mult FLOAT` — ASE global natural-cutoff multiplier
- `--ase-pair-cutoffs SPEC` — custom pair cutoffs such as `C-O:1.8,H-O:1.2`
- `--nopbc` — disable periodic boundary conditions
- `--cell`, `-c` — explicit 3x3 cell matrix values when PBC is enabled and input lacks cell info
- `-n`, `-np`, `--nproc` — process count
- `-s`, `--selectatoms` — select elements in the reaction network
- `--stepinterval INT` — read every N steps
- `--split INT` — split time axis into N parts
- `--maxspecies INT` — maximum number of nodes/species in the network
- `--matrixa a11 a12 a21 a22` — HMM transition matrix
- `--matrixb b11 b12 b21 b22` — HMM emission matrix
- `--urls FILENAME URL` — download files before analysis
- `--version`

## Parameter grouping for agents

### Always required

- input file(s): `-i`
- atom names: `-a`

If atom names are unknown for LAMMPS workflows, try to infer them from a nearby `.data` file before asking the user.

### Usually safe defaults

For quick sanity runs:

- `--nohmm`
- `--stepinterval 10`
- `--split 1`
- `--maxspecies 50`

These are workflow defaults, not official defaults.

### Official defaults worth remembering

From the official CLI page:

- `--nohmm`: default off
- `--miso`: default `0`
- `--type`: default `lammpsbondfile`
- `--ase-cutoff-mult`: default `1.2`
- `--nopbc`: default off
- `--stepinterval`: default `1`
- `--split`: default `1`
- `--maxspecies`: default `20`
- `--matrixa`: default `[0.999, 0.001, 0.001, 0.999]`
- `--matrixb`: default `[0.6, 0.4, 0.4, 0.6]`

## When to use native CLI instead of `rng-pipeline`

Prefer native `reacnetgenerator` if the request depends on official low-level flags such as:

- ASE bond-detection controls: `--use-ase`, `--ase-cutoff-mult`, `--ase-pair-cutoffs`
- explicit HMM matrix tuning: `--matrixa`, `--matrixb`
- selective graph construction: `--selectatoms`
- isomer merging behavior: `--miso`
- explicit cell / no-PBC handling beyond wrapper defaults
- explicit process-count tuning via `--nproc`
- URL-based download behavior via `--urls`

## Native CLI examples

### Bond trajectory

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type bond \
  -i bonds.reaxc \
  -a C H O \
  --nohmm
```

### Dump trajectory

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type dump \
  -i dump.reaxc \
  -a C H O \
  --nohmm
```

### XYZ trajectory with explicit cell

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type xyz \
  -i md.xyz \
  -a C H O \
  --nohmm \
  --cell 10 0 0 0 10 0 0 0 10
```

### ASE mode with custom pair cutoffs

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type xyz \
  -i md.xyz \
  -a C H O \
  --use-ase \
  --ase-cutoff-mult 1.2 \
  --ase-pair-cutoffs C-O:1.8,H-O:1.2
```

### HMM tuning

```bash
uvx --refresh --from reacnetgenerator reacnetgenerator \
  --type dump \
  -i dump.reaxc \
  -a C H O \
  --matrixa 0.999 0.001 0.001 0.999 \
  --matrixb 0.6 0.4 0.4 0.6
```

## Warnings

- `--dump` is deprecated; prefer `--type dump`.
- Do not pass `--cell` when the input already provides valid cell information unless there is a strong reason.
- Do not use `--nopbc` casually; it changes analysis semantics.
- If the user only wants inspection of existing outputs, prefer `rng-query` instead of rerunning analysis.
