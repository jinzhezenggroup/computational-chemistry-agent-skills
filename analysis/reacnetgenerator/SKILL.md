---
name: reacnetgenerator
description: Run ReacNetGenerator (native CLI) and/or reacnet-md-tools wrapper CLIs on reactive MD trajectories to generate reaction networks and reports. Triggers on requests like “run ReacNetGenerator on a LAMMPS dump/xyz/bond file”, “analyze .reactionabcd/.species”, “how to set PBC/cell vs --nopbc”, or “use ASE / miso / HMM matrices”.
---

# ReacNetGenerator

## 10-second quickstart

- Run a standard LAMMPS dump workflow:
  - `uvx --refresh --from reacnet-md-tools rng-pipeline ...`
- Analyze existing outputs (no rerun):
  - `uvx --refresh --from reacnet-md-tools rng-query ...`

If you need full official flags (e.g. `--cell`, `--nopbc`, `--use-ase`, `--miso`, HMM matrices), use native:

- `uvx --refresh --from reacnetgenerator reacnetgenerator ...`

## What this skill is for

Use this skill for **reactive MD post-processing** when the user wants to:

- run **ReacNetGenerator** on `bond`, `dump`, `xyz`, or `extxyz` trajectories
- handle common LAMMPS trajectory issues before running analysis
- choose between a **high-level wrapper** (`reacnet-md-tools`) and the **native `reacnetgenerator` CLI**
- inspect generated `.reactionabcd` / `.species` outputs after a run

## References (read only when needed)

Read only what is relevant:

- If the user asks about official flags or default values: [references/cli.md](references/cli.md)
- If the user asks about PBC/cell/`--nopbc` or input-type choice: [references/pbc-and-inputs.md](references/pbc-and-inputs.md)
- If the user wants copy-paste commands: [references/examples.md](references/examples.md)

## Tool-selection rule

Choose the narrowest tool that solves the user’s request:

1. **Use `rng-pipeline` by default** for standard LAMMPS dump workflows.
1. **Use native `reacnetgenerator`** when the user needs official low-level flags not exposed by the wrapper.
1. **Use `rng-query`** when the user already has `.reactionabcd` / `.species` outputs and wants analysis rather than rerunning.
1. **Use `rng-webapp`** only when the user explicitly wants an interactive local browser UI.

## Ask only for the missing inputs

Usually you only need:

- trajectory path(s)
- input type: `bond | dump | xyz | extxyz` if not obvious
- atom names for `-a/--atomname` unless they can be inferred from a LAMMPS data file
- whether the run should be treated as periodic, **only if cell information is missing or ambiguous**

Do **not** ask unnecessary questions when the trajectory already contains enough information.

## Default execution policy

### Preferred default: wrapper CLIs (`reacnet-md-tools`)

Use `reacnet-md-tools` for routine runs because it is safer and more agent-friendly:

- handles standard LAMMPS dump workflows
- can infer atom names from nearby `.data` files
- writes outputs into a predictable `out/<basename>/` directory
- reduces manual CLI assembly errors

When running the wrapper from an agent, prefer `uvx` so the latest published version is resolved automatically:

```bash
uvx --refresh --from reacnet-md-tools rng-pipeline --help
uvx --refresh --from reacnet-md-tools rng-query --help
```

### Fallback: native `reacnetgenerator`

Use native `reacnetgenerator` when the user explicitly needs official flags such as:

- `--miso`
- `--use-ase`
- `--ase-cutoff-mult`
- `--ase-pair-cutoffs`
- `--nopbc`
- `--cell`
- `-n/--nproc`
- `-s/--selectatoms`
- `--matrixa`
- `--matrixb`
- `--urls`

If using native CLI, follow the official flag semantics in [references/cli.md](references/cli.md).

## Decision rules

### Input type

- If the file clearly looks like a LAMMPS dump (`ITEM:` blocks), treat it as `dump`.
- If the input is a bond trajectory such as `bonds.reaxc`, treat it as `bond` / `lammpsbondfile`.
- If the input is `.xyz`, treat it as `xyz` unless it is explicitly `extxyz`.

### PBC / cell

Read [references/pbc-and-inputs.md](references/pbc-and-inputs.md) when choosing `--cell` or `--nopbc`.

Short version:

- For **LAMMPS dump/lammpstrj with valid `BOX BOUNDS`**, do **not** ask for `--cell`.
- For **XYZ without cell info**, ask whether the system should be treated as periodic.
- Use `--nopbc` only when the run is truly non-periodic, already unwrapped/reconstructed, or lacks meaningful periodic cell semantics.

### HMM

- For a quick first pass, use `--nohmm` unless the user explicitly wants HMM behavior.
- If the user asks for more faithful / publication-style treatment and knows what HMM means here, allow HMM by omitting `--nohmm`.

## Post-analysis rule

If the user already has outputs such as:

- `.reactionabcd`
- `.species`
- generated HTML / SVG / JSON reports

prefer **post-analysis** over rerunning. Use `rng-query` first unless the user specifically wants the raw files opened or a browser UI.

## Output expectations

For normal runs, make outputs predictable and easy to inspect:

- `run.log`
- generated `*.html`, `*.svg`, `*.json`, `*.species`, `*.reaction*`
- `summary.md` if using the wrapper workflow

## Working style

- Prefer non-interactive commands unless you truly have a TTY.
- Prefer explicit paths over implicit discovery when multiple candidate files exist.
- Stop and ask if atom-type inference is ambiguous.
- Do not invent unsupported flags; use the official CLI definitions from [references/cli.md](references/cli.md).

## Quick references

- Official CLI coverage: [references/cli.md](references/cli.md)
- Common recipes: [references/examples.md](references/examples.md)
- PBC and input decisions: [references/pbc-and-inputs.md](references/pbc-and-inputs.md)
