# LAMMPS + DeePMD-kit Reference Notes

This reference expands the main skill with practical operating guidance.

## When to use this skill

Use this skill when a user needs to:

- run LAMMPS with a DeePMD-kit model
- write or modify `input.lammps`
- explain what a LAMMPS command does
- switch between NVE, NVT, and NPT
- run through `uvx` in an internet-connected environment
- run through a site-installed `lmp` command in an offline or HPC environment

## Practical rules for agents

1. Prefer small, explicit input scripts over clever but opaque templates.
2. Explain every command in the example script, because many users treat the example as a starting point for their own production run.
3. If the user asks to run a simulation, always confirm the structure file and DeePMD model file before execution.
4. If the user asks for offline execution, ask which exact LAMMPS command should be used instead of guessing.
5. If the user only asks for a template, do not overcomplicate it with advanced computes or fixes unless they are needed.

## Suggested smoke test strategy

Before a long production run, consider a short test such as:

```lammps
run 100
```

This helps catch obvious issues such as:

- missing model file
- unsupported pair style in the local LAMMPS build
- malformed data file
- immediate numerical instability

Then replace the short run with the intended production length.

## Typical files in a DeePMD-LAMMPS job

- `input.lammps`: input script
- `data.system`: atomic structure and box
- `graph.pb` or `graph_compressed.pb`: DeePMD model
- `log.lammps`: main textual log
- `traj.lammpstrj`: trajectory output

## Caution points

- The correct timestep depends on the physical system and the DeePMD model quality.
- `velocity ... create ...` should usually not be repeated when continuing from a restart.
- NPT settings need physically sensible damping constants; avoid copying values blindly.
- Some local LAMMPS builds may support DeePMD under slightly different package configurations. Check `lmp -h` if unsure.
