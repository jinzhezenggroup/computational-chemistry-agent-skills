# computational-chemistry-agent-skills

Agent skills to run computational-chemistry tasks, used in OpenClaw

<!-- SKILLS_TABLE_START -->
## Skills Summary

| Skill | Description | Version | Compatibility |
|---|---|---|---|
| [lammps-deepmd](molecular-dynamics/lammps-deepmd/SKILL.md) | Run molecular dynamics simulations in LAMMPS with the DeePMD-kit plugin, including preparing input scripts, choosing ensembles such as NVE/NVT/NPT, validating commands against LAMMPS documentation, and executing jobs either with `uvx --from lammps --with deepmd-kit[gpu,torch] lmp` when internet access is available or with a user-specified offline LAMMPS executable. | 1.0 | Requires LAMMPS with DeePMD-kit support. Online mode prefers `uvx --from lammps --with deepmd-kit[gpu,torch] lmp`; offline mode requires a user-provided LAMMPS executable or module. |
| [dpdata-cli](tools/dpdata-cli/SKILL.md) | Convert and manipulate atomic simulation data formats using dpdata CLI. Use when converting between DFT/MD output formats (VASP, LAMMPS, QE, CP2K, Gaussian, ABACUS, etc.), preparing training data for DeePMD-kit, or working with DeePMD formats. Supports 50+ formats including deepmd/raw, deepmd/comp, deepmd/npy, deepmd/hdf5. | 1.0 | Requires uvx (uv) for running dpdata |
| [dpdisp-submit](tools/dpdisp-submit/SKILL.md) | Run Shell commands as computational jobs, on local machines or HPC clusters, through Shell, Slurm, PBS, LSF, Bohrium, etc. | 1.0 | Requires uv and access to the internet. |
| [openbabel](tools/openbabel/SKILL.md) | Use Open Babel CLI to convert molecular file formats, generate 3D structures from SMILES, render 2D structure images, and prepare Gaussian input files for computational chemistry workflows. | 1.1 | Requires uv and internet access (uses `uvx --from openbabel-wheel obabel ...`). |
| [unimol](tools/unimol/SKILL.md) | A robust, end-to-end CLI wrapper for Uni-Mol that standardizes molecular ML workflows. It enables one-line execution for representation extraction, model training, and property prediction, featuring built-in SMILES validation via RDKit for high-throughput reliability. | 1.0 | Requires uv. Dependencies (unimol-tools, rdkit, etc.) are handled automatically via inline script metadata in unimol_helper.py. |
<!-- SKILLS_TABLE_END -->
