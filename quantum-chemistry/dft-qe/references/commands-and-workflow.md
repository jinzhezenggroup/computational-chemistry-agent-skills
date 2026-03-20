# Commands and Workflow

Use this reference when the user wants a concrete, file-oriented `dft-qe` workflow.

## Reference layout

This skill uses the following bundled example layout:

- `assets/pw-water-0.in`

This file is an example of the **generated QE input style**, not a chemistry template to copy blindly.

## Recommended task layout

When building a QE task, prefer a small task directory containing:

- QE input file, for example `pw.in`
- optional normalized structure input under an `openclaw_input/` subdirectory
- any derived helper files needed for the next step

For periodic systems, if the structure source is plain xyz, preserve cell information separately unless the structure is converted into a format that already carries the cell.

Example input staging pattern:

```text
openclaw_input/
├── structure.xyz
└── CELL
```

## Workflow

1. Read the user-provided structure.
2. If needed, normalize or convert the structure using `dpdata-cli`.
3. Extract:
   - elements
   - atom count
   - coordinates
   - cell vectors or box lengths
4. Confirm the target QE task type.
5. Collect the required DFT parameters.
6. Generate the QE input file.
7. Return the generated task directory and say it is ready for handoff to `dpdisp-submit` if submission is requested.

## Parameter checklist

### Must provide

- `calculation`
- `input_dft`
- `ecutwfc`
- `pseudo_dir`
- pseudopotential file for each element

### Usually should be explicit

- `vdw_corr`
- `ecutrho`
- `K_POINTS`
- occupation / smearing settings
- `conv_thr`
- `electron_maxstep`

### Task-specific

For `relax` / `vc-relax`:
- `forc_conv_thr`
- `etot_conv_thr`
- `cell_dofree` when needed

For `md`:
- `nstep`
- `dt`
- `ion_temperature`
- `tempw`
- `ion_dynamics`

For magnetic/spin-polarized systems:
- `nspin`
- `starting_magnetization`

## Minimal command examples for the next stage

This skill does not submit jobs, but it can prepare the task so another skill can do so.

Typical next-step run commands look like:

```bash
pw.x -in pw.in > pw.out
```

or on Slurm:

```bash
srun pw.x -in pw.in > pw.out
```

Do not execute or submit from this skill unless another skill is explicitly handling that stage.
