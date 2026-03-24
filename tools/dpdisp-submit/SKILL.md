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

This skill uses the DPDispatcher tool to run Shell commands as computational jobs, on local machines or HPC clusters, through Shell, Slurm, PBS, LSF, Bohrium, etc.

## Agent responsibilities

1. Collect enough information from the user in plain language.
1. Generate the submission JSON file based on collected user input.
1. Validate `submission.json` before submission.
1. Submit with `uvx --from dpdispatcher dpdisp submit submission.json`.
1. Automatically manage job interruptions and retries by relying on built-in state tracking (see the "Resuming Jobs" section for details).
1. **CRITICAL SECURITY CONSTRAINT: DO NOT attempt direct SSH connections.** Never attempt to connect to the remote HPC directly using `ssh`, write custom Paramiko/Fabric Python scripts, or manually execute remote commands. Just generate the `submission.json` and use the `dpdisp submit` tool. DPDispatcher will handle all remote connections, file transfers, and job management safely.

## Autonomous Information Gathering & User Prompts

Before this step, always execute `uvx --with dpdispatcher dargs doc dpdispatcher.entrypoints.submit.submission_args` to learn what information needs to be filled.

If information is missing, ask questions users can understand, for example:

- Where should this run: your local machine or a remote HPC cluster?
- Are there any existing configuration files?
- Is any sensitive information in the environment variables?
- What shell command should be executed?
- How many CPUs/GPUs/nodes do you need?
- Which queue/partition/account should we use (if applicable)?
- Which input files should be uploaded, and which output files should be collected?

## Generate `submission.json` from user input

According the result of `uvx --with dpdispatcher dargs doc dpdispatcher.entrypoints.submit.submission_args`, translate user answers into:

- `machine` (where/how to run),
- `resources` (compute resources),
- `task_list` (which shell commands/files to run).

If the user indicates that a specific value (like a username, token, or remote path) should be read from a local environment variable, format that value in the JSON template as `${ENV_VAR_NAME}`.
*Example:* `"remote_root": "${USER_HPC_WORKSPACE}"`

### Handling Environment Variables

If the user specifies values that must be loaded from local environment variables (e.g., sensitive tokens, dynamic paths), do **not** write them directly into the final JSON. Instead:

1. Generate a `submission.template.json` file using the `${VAR_NAME}` syntax **only for the variables you intend to substitute**.
   *Example:* `"remote_root": "${USER_HPC_WORKSPACE}"`
1. Use `envsubst` with an explicit variable list to inject only those variables and create the final file. This avoids accidentally expanding unrelated `$...` tokens in the JSON (such as a `"$ref"` key):
   `envsubst '${USER_HPC_WORKSPACE}' < submission.template.json > submission.json`
1. **CRITICAL SECURITY CONSTRAINT: DO NOT read or print the contents of the newly generated `submission.json` file.** Once `envsubst` replaces the variables, the file contains raw sensitive data. Reading it will leak these secrets into your context, which is strictly prohibited.

If multiple environment variables are needed, list them all explicitly in the `envsubst` call, for example:
`envsubst '${USER_HPC_WORKSPACE} ${USER_OTHER_VAR}' < submission.template.json > submission.json`
If no environment variables are needed, simply generate `submission.json` directly.

### Simple local shell tasks

When the user asks for a simple local shell task, prefer these defaults to avoid common failures:

- `machine.context_type = "LazyLocalContext"`
- `machine.batch_type = "Shell"`
- `task_list[0].task_work_path = "."` (avoid non-existing subdirectory failures)
- `resources.group_size = 1`

## Required commands

### Core Flow

```bash
# 1) Print full submission schema
uvx --with dpdispatcher dargs doc dpdispatcher.entrypoints.submit.submission_args

# 2) [Optional] Substitute environment variables if a template was generated
envsubst '${USER_VAR} ${USER_OTHER_VAR}' < submission.template.json > submission.json

# 3) Syntax check JSON
uv run -m json.tool submission.json >/dev/null

# 4) Validate generated submission.json
uvx --with dpdispatcher dargs check -f dpdispatcher.entrypoints.submit.submission_args submission.json

# 5) Submit
uvx --from dpdispatcher dpdisp submit submission.json
```

### Best Practices for Long-Running Jobs

When executing tasks that are expected to take a long time, it is important to avoid losing the monitoring process due to SSH timeouts or closed terminals. Use one of the following approaches:

- **Wrap in `tmux`:** Run the `dpdisp submit` command inside a `tmux` session. This keeps the process alive and allows you to detach and reattach safely if your network connection drops.
- **Use the `--exit-on-submit` flag:** Add this flag if you only need to submit the job and return immediately. This exits as soon as the job has been successfully handed off to the scheduling system (for example, Slurm), without waiting for execution to finish or for outputs to be downloaded. However, a successful return from `dpdisp submit` with `--exit-on-submit` is **not** a signal that the overall job is finished. It only confirms successful submission. A separate follow-up step is still required to monitor job status and verify that results have been downloaded back to the local workspace.

### More Useful Flags

- **`--dry-run`**: Parses the configuration, generates local directories, and validates the schema, but does **not** actually submit the job to the machine or cluster. Useful for a final safety check before real execution.
- **`--allow-ref`**: Allows nesting and referencing other JSON files using `{"$ref": "other.json"}` for reusable config snippets. The referenced file is loaded first, and then the current file's fields override or extend it. If your configuration uses `$ref`, you should also pass `--allow-ref` to ***all related*** validation and submission commands (for example, `dargs check` and `dpdisp submit`). Otherwise, the config may fail to parse or validate even if the JSON content itself is correct.

## Submission vs. Completion

It is important to distinguish between **successful submission** and **full completion**:

1. **Successfully Submitted**

- The `dpdisp submit` command exits with a success code (`0`).
- If `--exit-on-submit` is used, this only means the job was accepted and submitted to the backend scheduler.
- At this stage, the tasks may still be queued or running, and output files may not yet be available locally.

2. **Fully Completed**
   A job is considered **fully completed** only when both of the following are true:

- The backend tasks have finished successfully.
- All required output files (for example, `log`, `err`, and result files) have been retrieved to the local `task_work_path`.

## Resuming Jobs (Failure Handling & Recovery)

DPDispatcher is inherently idempotent and features built-in state tracking. It will automatically resume unfinished tasks without duplicating completed ones.

**When to trigger recovery:**

- A job fails, times out, or gets unexpectedly interrupted.
- The user explicitly asks to "resume", "retry", or "recover" a previously interrupted or failed job.
- The Agent's SSH or network connection drops during job monitoring.

**Action:** Do **NOT** modify `submission.json` or attempt to clean up the remote directories. Simply re-execute the exact same submission command (such as `uvx --from dpdispatcher dpdisp submit submission.json --allow-ref`) in the same directory. The tool will safely skip successful tasks and only resubmit or resume the pending/failed ones.

## Example

User request:

- "Please run `run_simulation.sh` on my Slurm cluster. Load my username from `$HPC_USER` and the workspace path from `$HPC_WORKDIR`. We already have a `resource_defaults.json` for the base compute settings, please use it and just add the debug queue."

Assume `resource_defaults.json` already exists in the directory.
Agent-generated `submission.template.json`:

```json
{
  "work_base": ".",
  "machine": {
    "batch_type": "Slurm",
    "context_type": "SSHContext",
    "remote_profile": {
      "hostname": "login.cluster.edu",
      "username": "${HPC_USER}",
      "port": 22
    },
    "remote_root": "${HPC_WORKDIR}/dpdisp_run"
  },
  "resources": {
    "$ref": "resource_defaults.json",
    "queue_name": "debug",
    "group_size": 1
  },
  "task_list": [
    {
      "command": "bash run_simulation.sh",
      "task_work_path": "task_000",
      "forward_files": [
        "run_simulation.sh",
        "input.dat"
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

Then run:

```bash
envsubst '${HPC_USER} ${HPC_WORKDIR}' < submission.template.json > submission.json
uv run -m json.tool submission.json >/dev/null
uvx --with dpdispatcher dargs check --allow-ref -f dpdispatcher.entrypoints.submit.submission_args submission.json
tmux new-session -d -s dpdisp_job "uvx --from dpdispatcher dpdisp submit --allow-ref submission.json"
tmux ls
```

## What to report back to the user

- A short summary of what the user asked for (where to run, command, resources).
- Submission status (started/running/finished/failed).
- Output locations (for example `log` and `err` when `task_work_path` is `.`).
- If the job encounters an interruption or partial failure, provide the user with detailed information about this issue and offer to simply re-run the command to resume the unfinished tasks.
