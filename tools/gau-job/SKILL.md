---
name: gau-job
description: Run Gaussian calculations from a .gjf input on local or remote/HPC environments: confirm Gaussian executable/setup (module/source/path), working directories, log filenames, and GAUSS_SCRDIR scratch; then provide a runnable command template with placeholders.
metadata:
  author: light-cyan
  version: "0.1.0"
---

## Ask the user for these details

- Run location: `<local>` or `<remote/HPC>` (and scheduler if any)
- Environment setup: `<env_setup_cmds>` (e.g. module load / source script)
- Gaussian executable: `<gaussian_exec>` (e.g. `g16`, `g09`, or absolute path)
- Working directory:
  - local prep dir: `<local_work_dir>` (if applicable)
  - remote run dir: `<remote_work_dir>` (if applicable)
  - per-task dir: `<task_work_dir>`
- Files:
  - input: `<input.gjf>`
  - Gaussian output: `<gaussian_log>`
  - wrapper stdout/stderr (if needed): `<stdout_log>`, `<stderr_log>`
- Scratch:
  - `GAUSS_SCRDIR=<scratch_dir>` (e.g. `./scratch`, `$TMPDIR`, or site-provided scratch)
  - whether to clean scratch after the run

## Command template

```bash
<env_setup_cmds>
export GAUSS_SCRDIR=<scratch_dir>
mkdir -p "$GAUSS_SCRDIR"

<gaussian_exec> < <input.gjf> > <gaussian_log>

rm -rf "$GAUSS_SCRDIR"
```

## Generate / assemble `.gjf` (when needed)

Use **gjf-flux** to extract/assemble `.gjf` sections and build workflows.

Read: `reference/gjf-flux/SKILL.md`

## Submit via dpdispatcher (recommended)

Recommend using dpdispatcher to submit Gaussian calculations.

Find the submission skill: `dpdisp-submit`
