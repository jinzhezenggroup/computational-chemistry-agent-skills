---
name: dpdisp-submit
description: >
  Run Shell commands as computational jobs, on local machines or HPC clusters, through Shell, Slurm, PBS, LSF, Bohrium, etc.
  USE WHEN the user needs to submit batch jobs to a cluster, run commands on a remote server, execute tasks via job schedulers (Slurm, PBS, LSF), or safely run long-term/background shell commands that require state tracking and auto-recovery.
compatibility: Requires uv and access to the internet.
license: LGPL-3.0-or-later
metadata:
  author: deepmodeling
  version: '1.0'
---

# dpdisp-submit

This Skill guides the Agent to use the DPDispatcher tool to convert Shell commands into computational jobs and submit them to local machines or High-Performance Computing (HPC) clusters (supporting environments such as Shell, Slurm, PBS, LSF, Bohrium, etc.).

## Syntax & Protocol

This section defines the field mappings, variable syntax, and special flags for the configuration file.

### Protocol Acquisition (Initialize)

As an Agent, before gathering information and building the configuration, you **MUST FIRST execute** the following command to read and learn the latest Schema protocol specifications and requirements:

```bash
uvx --with dpdispatcher dargs doc dpdispatcher.entrypoints.submit.submission_args
```

### Field Mapping

You must accurately translate the gathered user requirements into the following core JSON hierarchy:

- `machine`: Defines the execution location and method (connection protocol, scheduler type).
- `resources`: Defines the computational resource requirements (nodes, CPUs, GPUs, queues, etc.).
- `task_list`: Defines the specific Shell commands to be executed and the file flow paths.

### Environment Variable Syntax & Injection Rules

If user-specified values (e.g., username, Token, remote path) need to be read from local environment variables, you must strictly use the `${ENV_VAR_NAME}` format in the template.

- *Example:* `"remote_root": "${USER_HPC_WORKSPACE}"`

### Reference & Reuse

The protocol allows the use of the `{"$ref": "other.json"}` syntax to nest and reference reusable configuration snippets from other JSON files (the referenced file is loaded first, and then the current file's fields override or extend it). The relative path for `$ref` is resolved relative to the execution directory where `submission.json` is located. You must ensure that the execution path strictly matches the path pointed to by `$ref`.

### Path Resolution Rules

- **Base Directory (`work_base`)**: Defines the base working directory level for all tasks, typically set to `.` (i.e., the current execution directory).
- **Task and File Path Resolution**: `task_work_path` is resolved relative to `work_base`, whereas the file paths specified in `forward_files` are strictly resolved relative to `task_work_path`.

### Dry-Run Testing (--dry-run)

Parses the configuration, generates local directories, and validates the Schema, but **DOES NOT** actually submit the job to the machine or cluster. You can use this flag for a final safety check before real execution.

## Execution Workflow

As an Agent, you MUST strictly execute tasks in the sequence of the following stages, without skipping any steps:

### Information Gathering

When feeling vague or uncertain about the specific parameters and configuration information for running the job, you **MUST** proactively ask the user in natural language to supplement the necessary information.

### Secure Build

You **MUST** generate the configuration file based on the acquired Schema protocol and the gathered information.

- **Pure Static Configuration**: If no environment variable injection is needed, directly generate the final `submission.json`.
- **Environment Variable Injection Required**:
  - You must generate a `submission.template.json` file, using the `${VAR_NAME}` syntax **ONLY for the variables that need to be replaced**.
  - You must use the `envsubst` command and **explicitly list** the variables to be replaced to prevent unrelated `$…` symbols in the JSON (such as `"$ref"`) from being accidentally expanded.
  - *Example:*
    ```bash
    envsubst '${USER_HPC_WORKSPACE} ${USER_OTHER_VAR}' < submission.template.json > submission.json
    ```

### Validate & Submit

You **MUST** strictly execute the following command chain in sequence.
**Note**: If the `$ref` syntax is used in the configuration, you must pass the `--allow-ref` flag to all validation and submission commands, otherwise parsing or validation will fail even if the JSON content is correct.

```bash
# Logic and Schema Validation
uvx --with dpdispatcher dargs check -f dpdispatcher.entrypoints.submit.submission_args submission.json
# Submit Job
uvx --from dpdispatcher dpdisp submit submission.json
```

### Reporting Standard

After execution finishes, you **MUST** output a structured report to the user with the following fixed elements:

- **Task Summary**: Briefly describe the user's request (execution location, executed command, allocated resources).
- **Current State**: Explicitly point out the status of the job (started / running / finished / failed).
- **Artifact Path**: Explicitly point out the location of the output files (for example, when `task_work_path` is `.`, point out the specific paths of `log` and `err`).
- **Exception Guidance**: If the job encounters an interruption or partial failure, provide the user with detailed issue information and execute according to the user's further instructions.

## Long-Running Jobs

High-performance computing tasks usually take an extremely long time (from hours to weeks), and there is a **long time gap** between the submission command and the final result. This is **not a one-off, instant Q&A process**, and you must choose the appropriate disconnect-prevention execution mode based on the specific scenario:

### Blocking Mode

- **Wrap in `tmux`**: Run the standard `dpdisp submit submission.json`. The program will **continuously hang and wait** until the job is truly finished calculating on the cluster and the files are downloaded back before exiting. You must run it inside a `tmux` session to prevent any possible disconnection from killing the process.

### Non-blocking Mode

- **Use the `--exit-on-submit` flag**: After successfully handing over the job to the scheduling system (e.g., Slurm), the program will **immediately exit the terminal** and return `<exit_code>`. It will not wait for execution to complete or download outputs.
- **State Definition**: In this mode, you must strictly distinguish between the following two states for the user:
  - **Successfully Submitted (Submitted)**: Just finished executing the command with the flag and returned `0`. At this time, the job is only accepted by the backend, may be queuing, and output files are temporarily unavailable.
  - **Fully Completed (Completed)**: After re-running the synchronization command later, the backend task finishes successfully, **AND** all required output files have been successfully retrieved to the local machine.
- **Idempotent Recovery Principle (Resuming Jobs)**: DPDispatcher has built-in state tracking and idempotency. It will automatically resume unfinished tasks and will not repeatedly execute completed ones.
  - **Trigger Conditions**: Used for **state synchronization and file downloading** in non-blocking mode; or when the job fails, times out, is unexpectedly interrupted, the user explicitly requests to "resume" or "retry", or your own SSH/network disconnects during monitoring.
  - **Recovery Action**: You do not need to modify `submission.json` or attempt to clean up the remote directory. You simply need to **re-execute the exact same** submission command (e.g., `uvx --from dpdispatcher dpdisp submit submission.json --allow-ref`) as is in the same directory.

> **Timeline Example (Non-blocking Mode):**
>
> - **[Day 1, 10:00]** Submit job: `dpdisp submit --exit-on-submit submis_task.json`
> - **[Day 1, 10:01]** The command exits immediately and returns 0. At this time, it is only in the **Successfully Submitted** state. The Agent can exit the terminal to execute other tasks.
> - **[Waiting Period]** *(A long queuing and calculation phase, potentially lasting for days)*
> - **[Day 3, 15:00]** The Agent returns to the directory to check: triggers the idempotent recovery mechanism, re-runs `dpdisp submit submis_task.json` **without the flag** as is to synchronize the state and trigger file downloading. Only after the download is complete is it marked as **Fully Completed**.

## Strict Guardrails

Before performing any operation, as an Agent, you **MUST UNCONDITIONALLY obey** the following security baselines:

- **Direct SSH Connections are Strictly Prohibited**: You are absolutely not allowed to attempt connecting directly to the remote HPC using `ssh`, write custom Paramiko/Fabric Python scripts, or manually execute remote commands. All remote connections, file transfers, and job management **MUST AND ONLY** be safely handled by DPDispatcher by generating `submission.json` and calling the `dpdisp submit` tool.
- **Reading External Reference JSON Files is Strictly Prohibited**: If the user provides a JSON file to supply certain information, you are **ABSOLUTELY PROHIBITED** from reading or printing the contents of that file. The file contains raw sensitive data, and reading it will cause confidential information to leak into the current conversation context.
- **Reading Configuration Files with Sensitive Data is Strictly Prohibited**: After injecting environment variables via `envsubst` to generate the final `submission.json`, you are **ABSOLUTELY PROHIBITED** from reading or printing the contents of the file. The file contains raw sensitive data, and reading it will cause confidential information to leak into the current conversation context.

## Example

User request: "Please run the simulation located in the `task02` directory on my Slurm cluster. Load my username from `$HPC_USER` and the workspace path from `$HPC_WORKDIR`. We already have a `resource_defaults.json` in the parent workspace directory, please reference it and just add the debug queue."

The Agent discovers that the current directory structure is as follows:

```text
<WORKSPACE>/
├── resource_defaults.json
├── ...
└── run_dir/
    ├── ...
    └── task02/
        ├── run_simulation.sh
        ├── ...
        └── data/
            ├── input.dat
            └── ...
```

The Agent decides to create the configuration file `submis_task02.template.json` within the `run_dir/` directory (at the same level as the `task02/` folder).
The Agent has remembered the `$ref` pointing to the parent directory `../`, the `task_work_path` explicitly targeting `"task02"`, and `forward_files` remaining strictly relative to that `task_work_path`.
Then it writes down:

```json
{
  "work_base": ".",
  "machine": {
    "batch_type": "Slurm",
    "context_type": "SSHContext",
    "remote_profile": {
      "hostname": "<target-host>",
      "username": "${HPC_USER}",
      "port": 22
    },
    "remote_root": "${HPC_WORKDIR}/dpdisp_run"
  },
  "resources": {
    "$ref": "../resource_defaults.json",
    "queue_name": "debug",
    "group_size": 1
  },
  "task_list": [
    {
      "command": "bash run_simulation.sh",
      "task_work_path": "task02",
      "forward_files": [
        "run_simulation.sh",
        "data/input.dat"
      ],
      "backward_files": [
        "result.out",
        "log",
        "err"
      ]
    }
  ]
}
```

Then the Agent run the validation and submission commands from within the `<WORKSPACE>` directory:

```bash
cd run_dir/
envsubst '${HPC_USER} ${HPC_WORKDIR}' < submis_task02.template.json > submis_task02.json
uvx --with dpdispatcher dargs check --allow-ref -f dpdispatcher.entrypoints.submit.submission_args submis_task02.json
tmux new-session -d -s dpdisp_task02 "uvx --from dpdispatcher dpdisp submit --allow-ref submis_task02.json"
tmux ls
```
