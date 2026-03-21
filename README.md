# Computational Chemistry Agent Skills

This repository hosts [Agent Skills](https://agentskills.io/home) to run computational-chemistry tasks.
These skills can be installed and used in [OpenClaw](https://github.com/openclaw/openclaw), enabling OpenClaw to run complex computational-chemistry workflows.

A website, [https://skills.jinzhezeng.group](https://skills.jinzhezeng.group), is hosted to view all skills.

## Install the skills

Copy/paste this message to your OpenClaw agent.

```md
Please install ALL skills from computational-chemistry-agent-skills on the OpenClaw host.

Goal
- Install each skill as its own folder directly under: ~/.openclaw/skills/
  (OpenClaw discovers skills at <skillsRoot>/*/SKILL.md; it will NOT recursively scan deeper trees.)

Steps
1) Download repository ZIP: https://github.com/jinzhezenggroup/computational-chemistry-agent-skills/archive/refs/heads/master.zip
2) Unzip it to get: computational-chemistry-agent-skills-master/
3) Find every SKILL.md in the repo and copy its parent folder into ~/.openclaw/skills/<folder-name>/
4) Start a NEW OpenClaw session so skills reload

Verify
openclaw skills list --eligible
```

<!-- SKILLS_TABLE_START -->
## Skills Summary

| Skill | Description | Version | Compatibility |
|---|---|---|---|
| [agent-taskboard-manifest](agent-workflow/agent-taskboard-manifest/SKILL.md) | It is a specification for semantic workflows used by agents to plan, generate, formalize, summarize, and execute complex tasks, projects, experiments, and research efforts for agents, requiring explicit structure, lazy loading, scoped context, evidence-grounded routing, and human review at critical checkpoints. USE WHEN the user asks for a complex task, project, experiment, or research effort that needs to be carefully planned before execution USE WHEN the user provides a text-based plan and wants it to be made more detailed and formalized according to this specification. USE WHEN the user asks to summarize ongoing or completed work into a reusable workflow manifest. USE WHEN the user specifies the location of an existing agent workflow and wants it loaded and executed according to the specification. | 0.1.0 | - |
| [reacnetgenerator](analysis/reacnetgenerator/SKILL.md) | Run ReacNetGenerator on LAMMPS trajectories to generate reaction networks and reports. Use when the user wants to analyze reactive MD trajectories with ReacNetGenerator (dump/xyz/bond). Handles common LAMMPS dump quirks like x/y/z vs xs/ys/zs scaled coordinates by converting to x/y/z (orthorhombic + triclinic supported via reacnet-md-tools >= 0.1.1), infers atomname order from a LAMMPS data file when available, runs via local reacnetgenerator or via `uvx --from reacnetgenerator`, and writes outputs into `out/<input_basename>/` with logs and a summary. | 1.0 | Requires uv and internet access (uses `uvx --from reacnet-md-tools ...` and `uvx --from reacnetgenerator ...`). |
| [dpdata-cli](data-processing/dpdata-cli/SKILL.md) | A command-line utility for converting and manipulating over 50 atomic simulation data formats, including outputs from DFT and MD software (VASP, LAMMPS, Gaussian, QE, CP2K, ABACUS, etc.). USE WHEN you need to convert structural or trajectory files between different computational chemistry formats, or when parsing raw simulation outputs into structured training datasets (e.g., deepmd/raw, deepmd/npy, deepmd/hdf5) for DeePMD-kit. | 1.0 | Requires uvx (uv) for running dpdata |
| [openbabel](data-processing/openbabel/SKILL.md) | A versatile CLI tool for converting molecular file formats, generating 3D atomic coordinates from SMILES, rendering 2D chemical structure images, and preparing or extracting structures for computational workflows. USE WHEN you need to convert between chemical file formats (e.g., xyz, pdb, mol, smi, gjf), generate 3D structures from SMILES using `--gen3d`, render molecule images (PNG/SVG), or extract geometries from simulation logs to build new inputs. | 1.1 | Requires uv and internet access (uses `uvx --from openbabel-wheel obabel ...`). |
| [packmol-generate-mixture](data-processing/packmol-generate-mixture/SKILL.md) | A tool for generating initial packed molecular configurations (XYZ format) from single-molecule structures by calculating box dimensions, writing input scripts, and executing Packmol. USE WHEN you need to randomly pack a specific number of molecules into a simulation box (defined by target density or fixed lengths) to create starting geometries for molecular dynamics or related computational chemistry workflows. | 1.0 | Requires uv and internet access (uses `uvx packmol ...`). |
| [deepmd-finetune-dpa3](machine-learning-potentials/deepmd-finetune-dpa3/SKILL.md) | Fine-tune a DPA3 model in DeePMD-kit using the PyTorch backend. Use when the user wants to adapt a pre-trained DPA3 model to a new downstream dataset. Supports fine-tuning from a self-trained DPA3 model (.pt checkpoint), from a multi-task pre-trained model, or from a built-in pretrained model downloaded via `dp pretrained download` (e.g., DPA-3.1-3M, DPA-3.2-5M). Covers single-task and multi-task fine-tuning workflows. | 1.0 | Requires deepmd-kit with PyTorch backend installed. GPU strongly recommended. |
| [deepmd-python-inference](machine-learning-potentials/deepmd-python-inference/SKILL.md) | Run Python inference with DeePMD-kit models using the DeepPot API. Use when the user wants to load a trained/frozen DeePMD model (.pth or .pb) or a built-in pretrained model (e.g., DPA-3.2-5M) in Python, predict energy/force/virial for atomic configurations, evaluate descriptors, or calculate model deviation between multiple models. Also covers using `dp test` CLI for batch evaluation against labeled data. | 1.0 | Requires deepmd-kit Python package installed. PyTorch backend for .pth models, TensorFlow for .pb models. |
| [deepmd-train-dpa3](machine-learning-potentials/deepmd-train-dpa3/SKILL.md) | Train a DeePMD-kit model using the DPA3 descriptor with the PyTorch backend. Use when the user wants to train a state-of-the-art deep potential model based on message passing on Line Graph Series (LiGS). DPA3 provides high accuracy and strong generalization, suitable for large atomic models (LAM) and diverse chemical systems. Supports both fixed and dynamic neighbor selection. | 1.0 | Requires deepmd-kit with PyTorch backend installed. GPU strongly recommended. Custom OP library required for LAMMPS deployment. |
| [deepmd-train-se-e2-a](machine-learning-potentials/deepmd-train-se-e2-a/SKILL.md) | Train a DeePMD-kit model using the SE_E2_A (DeepPot-SE) descriptor with the PyTorch backend. Use when the user wants to train a classical deep potential model for a specific system, prepare training input JSON, run `dp --pt train`, monitor learning curves, freeze the model, and test it. SE_E2_A is the foundational two-body embedding descriptor suitable for most condensed-phase systems. | 1.0 | Requires deepmd-kit with PyTorch backend installed. GPU recommended for production training. |
| [lammps-deepmd](molecular-dynamics/lammps-deepmd/SKILL.md) | A tool and knowledge base for running molecular dynamics (MD) simulations in LAMMPS with the DeePMD-kit plugin. It handles input script preparation, ensemble selection (NVE/NVT/NPT), and job execution via `uv` or offline binaries. USE WHEN you need to set up, write, explain, or execute a LAMMPS molecular dynamics simulation using a DeePMD machine learning potential (e.g., `graph.pb`). | 1.0 | Requires LAMMPS with DeePMD-kit support. Online mode prefers `uvx --from lammps --with deepmd-kit[gpu,torch,lmp] lmp`; offline mode requires a user-provided LAMMPS executable or module. |
| [unimol](molecular-representation/unimol/SKILL.md) | A standardized CLI wrapper for Uni-Mol molecular ML workflows that handles representation extraction (embeddings), model training (regression/classification), and property prediction with built-in RDKit SMILES validation. USE WHEN you need to generate molecular embeddings, train machine learning models for chemical properties, or run predictions on SMILES datasets (.csv/.smi) using the Uni-Mol framework. | 1.0 | Requires uv. Dependencies (unimol-tools, rdkit, etc.) are handled automatically via inline script metadata in unimol_helper.py. |
| [dft-qe](quantum-chemistry/dft-qe/SKILL.md) | Generate Quantum ESPRESSO DFT input tasks from a user-provided structure plus user-specified DFT settings. Use when the user wants to prepare QE calculations such as SCF, NSCF, relax, vc-relax, MD, bands, DOS, or phonons starting from a structure file or coordinates together with pseudopotentials, functional choice, cutoffs, k-point settings, smearing, spin/charge, and convergence parameters. This skill prepares the QE task only; use a separate submission skill such as dpdisp-submit to submit the generated task. | 1.3 | Requires a user-provided initial structure and enough DFT parameters to build a scientifically meaningful QE input. |
| [gjf-flux](quantum-chemistry/gjf-flux/SKILL.md) | Assemble and extract Gaussian .gjf input file sections (directives, route, title, molecule blocks, appendices) and build single- or multi-step Link1 jobs from modular component files. USE WHEN needed for generating, refactoring, templating, or scripting Gaussian job files. | 0.1.0 | Requires `uv` installed and available in PATH. |
| [run-gauss](quantum-chemistry/run-gauss/SKILL.md) | Acts as a knowledge base providing environment checklists, directory/scratch management, and bash command templates. USE WHEN you need to guide the execution of Gaussian computational chemistry jobs (.gjf) on local or remote/HPC environments. | 0.1.0 | - |
| [dpdisp-submit](tools/dpdisp-submit/SKILL.md) | Run Shell commands as computational jobs, on local machines or HPC clusters, through Shell, Slurm, PBS, LSF, Bohrium, etc. USE WHEN the user needs to submit batch jobs to a cluster, run commands on a remote server, execute tasks via job schedulers (Slurm, PBS, LSF), or safely run long-term/background shell commands that require state tracking and auto-recovery. | 1.0 | Requires uv and access to the internet. |
| [search-species](tools/search-species/SKILL.md) | USE WHEN requesting core chemical structural data (SMILES, formula, mass, 2D images) via IUPAC, common, or multilingual names. You MUST actively retrieve the data using this skill; DO NOT hallucinate or generate structures yourself. DO NOT USE WHEN asking for physical properties (melting point, solubility), safety/toxicity data (MSDS), or synthesis pathways. | 0.1.0 | Requires `uv` installed. |
<!-- SKILLS_TABLE_END -->

## License

This project is licensed under GNU [LGPLv3.0](LICENSE).
