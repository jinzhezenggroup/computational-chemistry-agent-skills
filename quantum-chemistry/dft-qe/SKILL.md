---
name: dft-qe
description: Generate Quantum ESPRESSO DFT input tasks from a user-provided structure plus user-specified DFT settings. Use when the user wants to prepare QE calculations such as SCF, NSCF, relax, vc-relax, MD, bands, DOS, or phonons starting from a structure file or coordinates together with pseudopotentials, functional choice, cutoffs, k-point settings, smearing, spin/charge, and convergence parameters. This skill prepares the QE task only; use a separate submission skill such as dpdisp-submit to submit the generated task.
compatibility: Requires a user-provided initial structure and enough DFT parameters to build a scientifically meaningful QE input.
license: MIT
metadata:
  author: OpenClaw
  version: '1.3'
---

# DFT with Quantum ESPRESSO

Use this skill to **build a QE DFT task** from a user-provided structure and DFT settings.

## Scope

This skill should:
- require a user-provided structure
- read or normalize the structure input
- identify the target calculation type
- collect the minimum required DFT settings
- generate the QE input file
- organize the task directory in a way that can be handed off to a submission skill
- state assumptions and unresolved choices

This skill should **not**:
- submit jobs
- manage schedulers
- handle remote execution
- invent critical scientific parameters

If the user wants the task submitted, hand off to another skill such as `dpdisp-submit` after the QE task is generated.

## Hard requirement

The user must provide a structure.

Do not generate a QE task without a user-provided structure source. If the structure is missing, stop and ask for it.

## Structure input convention

Use this bundled example-plus-layout pattern as the reference:

- generated QE input example: `assets/pw-water-0.in`
- user-provided structure staging pattern: `openclaw_input/` containing files such as `structure.xyz` and `CELL`

Treat this as the canonical pattern for what the user is expected to provide and what this skill is expected to generate.

The structure format does **not** need to be fixed to xyz. If the user provides another reasonable atomistic structure format, convert or normalize it as needed. When format conversion is needed, use the `dpdata-cli` skill.

For periodic systems, ensure cell information is preserved. If a plain xyz file is used, cell data must be provided separately, for example through a `CELL` file.

For a concrete file-oriented workflow, see `references/commands-and-workflow.md`.

## Expected workflow

1. Start from a user-provided structure.
2. Normalize the structure into the task layout if needed.
3. Determine the target QE calculation type.
4. Collect only the missing critical DFT parameters.
5. Generate the QE input file.
6. Place the generated task in a runnable task directory.
7. If submission is requested, pass that directory to `dpdisp-submit`.

## DFT parameters to collect

### Must provide

Do not generate a formal QE task unless these are known or explicitly confirmed:

- `calculation`
- `input_dft`
- `ecutwfc`
- `pseudo_dir`
- pseudopotential file for each element

### Usually should be explicit

These should normally be confirmed rather than guessed:

- `vdw_corr` when dispersion may matter
- `ecutrho` when relevant to the pseudopotential family or workflow
- `K_POINTS` setting, for example `gamma` or an automatic mesh
- occupation / smearing settings for metallic or ambiguous systems
- `conv_thr`
- `electron_maxstep`

### Task-specific additions

Also collect task-dependent parameters when relevant.

For `relax` / `vc-relax`:
- `forc_conv_thr`
- `etot_conv_thr`
- `cell_dofree` for `vc-relax`

For `md`:
- `nstep`
- `dt`
- `ion_temperature`
- `tempw`
- `ion_dynamics`

For spin-polarized or magnetic systems:
- `nspin`
- `starting_magnetization`
- charge or spin-related settings if requested

For advanced workflows if explicitly requested:
- Hubbard U settings
- hybrid-functional settings
- electric field settings such as `edir`, `emaxpos`, or related controls

Do not ask for everything at once; ask only for the missing essentials.

## Required behavior

1. Inspect the provided structure if accessible.
2. Determine elements, cell information, and coordinate representation.
3. If format normalization is needed, convert the structure using `dpdata-cli`.
4. Confirm the QE task type.
5. Gather only the missing critical DFT settings.
6. Generate the QE input yourself.
7. Explain assumptions clearly.
8. Flag unresolved scientific choices instead of hiding them.
9. Prepare the task directory so another skill can submit it.

## Template pattern

Use the QE example input included in this repository:

`assets/pw-water-0.in`

as the reference pattern for how a QE task is organized and how the `pw.x` input is laid out.

In this workflow:
- the user provides the structure in `openclaw_input`-style form
- this skill generates the QE input task, analogous to files like `assets/pw-water-0.in`
- a separate submission skill handles the job script and submission stage

Do not hard-code the example chemistry. Reuse only the workflow pattern.

## Defaulting policy

Allowed only for low-risk, clearly labeled assumptions.

Reasonable provisional defaults:
- `calculation='scf'` for a plain single-point request
- standard electronic convergence threshold when the user does not care
- basic verbosity settings

Do **not** silently invent:
- structure data
- pseudopotential filenames
- production cutoffs
- production k-point meshes
- magnetic state for open-shell systems
- Hubbard / vdW / hybrid settings
- metallic smearing behavior when the system character is unclear

## Expected output

Provide:
1. the full QE input file
2. a short summary of the chosen settings
3. explicit assumptions
4. any decisions the user should still confirm
5. the generated task directory or file set for the next skill
6. if submission is requested, explicitly say the next step is `dpdisp-submit`

## Minimal `pw.x` structure

```text
&CONTROL
  calculation = 'scf'
  prefix = 'system'
  outdir = './'
/
&SYSTEM
  ibrav = 0
  nat = ...
  ntyp = ...
  ecutwfc = ...
  ecutrho = ...
/
&ELECTRONS
  conv_thr = 1.0d-8
/
ATOMIC_SPECIES
...
CELL_PARAMETERS angstrom
...
ATOMIC_POSITIONS angstrom
...
K_POINTS automatic
kx ky kz 0 0 0
```

## Handoff rule

When the user asks to submit the generated QE task, do not implement submission logic here. Instead:
- finish generating the QE task directory and input file
- tell the user the task is ready for submission
- hand off to `dpdisp-submit`

## Common failure points

- missing user-provided structure
- missing cell for periodic systems
- incomplete pseudopotential mapping
- `nat` / `ntyp` inconsistent with the structure
- missing or poor cutoffs
- missing or inappropriate smearing
- omitted spin settings for magnetic cases
- requesting post-processing or phonons without prerequisite context
