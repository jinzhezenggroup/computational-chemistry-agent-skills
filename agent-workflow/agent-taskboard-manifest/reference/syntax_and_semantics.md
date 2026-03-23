# Syntax and Semantics

This specification defines the physical file organization, internal data structures, and core logical semantics of the `AgentTaskboardManifest`.

## Directory Structure and Scope

Workflows are organized in closed, independent directories. The standard topology is as follows:

- `-workflow.yaml`: **Global Context**. Defines the purpose, macro boundaries, global conventions, and final success criteria of the workflow.
- `!entry.task.yaml`: **Entry Node**. The first loaded object during workflow initialization.
- `*.task.yaml`: **Sub-task Nodes**. Reusable, concrete execution units; supports relative path referencing (e.g., `./xyz.task.yaml`).

## `-workflow.yaml`

Used to establish global execution boundaries and set up the Global Context.

```yaml
workflow_id: <goal_task_name>
domain: <business_domain>      # The business domain (e.g., Computational Chemistry, Data Processing)
applicable_if:                 # Applicable scenarios
  - <scenario_description>
not_applicable_if:             # Inapplicable scenarios (hitting this should result in execution rejection)
  - <exclusion_condition>
non_goals:                     # Overall boundaries (explicitly stating what NOT to do, preventing scope creep)
  - <out_of_scope_behavior>
success_criteria:              # Success criteria
  - <observable_outcome>
prerequisites:                 # Global prerequisite dependency declarations
  <dependency>: <requirement_description_and_verification_method>
  # Example: `python_env: "Require Python 3.10 or higher. Execute 'python --version' to verify compatibility."`

global_conventions:            # Global conventions
  <convention>: <rule_description_and_constraint>
  # Example: `workspace_dir: "Required. The root directory of the current workflow, absolute path."`
  # Example: `units: "Time in seconds, distance in Angstroms."`
assumptions:                   # Underlying assumptions
  - <environmental_assumption>
  # Example: `"Network connection is stable."`
  # Example: `"User is logged into the VPN."`
  # Example: `"Data provided by the user is already cleaned."`
```

## `*.task.yaml`

The smallest functional unit of execution. It declares the I/O contract, environment requirements, and execution sequence.

```yaml
task_id: <task_identifier>                   # Unique task identifier (e.g., "submit_slurm_job")
purpose: <task_objective_description>        # The objective of this task

prerequisites:                 # Prerequisite dependency declarations for this specific task
  <dependency>: <requirement_description_and_verification_method>
  # Example: `slurm_access: "Must have partition submission rights. Run 'sinfo' to check cluster status."`

# --- The I/O contract for the entire Task is declared here, used to centrally define and specify all variables that will be utilized in subsequent steps.
inputs:                        # Input Definition
  # The sources of variables can be:
  # - Context: Implicitly passed by the calling parent task.
  # - Dynamic: Initially described as "unknown", but dynamically generated via tools during the internal execution of a <step_object>.
  # - Human-in-the-loop: Initially described as "unknown", but actively requested from the user within a specific <step_object>.
  <variable>: <source_and_semantic_constraint>
  # Example: `gjf_file: "Required. The Gaussian input file to be processed; Sourced from upstream context; .gjf format."`
  # Example: `password: "Optional. Password to connect to the target server; Initially 'unknown', if public key auth fails; Request from user in a subsequent step."`
outputs:                       # Output Definition
  <variable>: <output_description_and_constraint>
  # Example: `job_id: "The numeric ID string returned after successfully submitting to Slurm."`

steps:                         # Execution instruction sequence (executed sequentially by default)
  - <step_object>
```

## `<step_object>`

The atomic operational unit within the task sequence. Contains behavioral actions, expected artifacts, self-validation, and routing jumps.

```yaml
  - id: <step_id>                                           # Step identifier, facilitates routing jumps
    action: <executable_action_description>                 # Core action. Directly describe the behavior the Agent needs to execute using natural language.
  # Examples:
  # - `"Load skill '<name of the agent skill>'"`
  # - `"Execute sub-task './prepare_data.task.yaml'"`
  # - `"Run shell command 'pytest tests/'"`
  # - `"Request user to review the intermediate results and confirm before proceeding."`
  # - `"Search the web for the latest Python documentation"`
  # - `"Inquire user: 'Do you want to overwrite?' (options: [yes, no])"`
  # - `"Inquire user: 'What substance do you want to inquire about?'"`

    notes:
      - <execution_note_or_warning>                         # Execution notes (e.g., "This command might hang, please set timeout to 60s")
    produces:                                               # Intermediary middleware/artifacts produced by the step
      <artifact>: <artifact_description_and_use>
    # Example: `temp_log: "Stdout text generated by running the command, used for regex extraction."`
    checks:                                                 # Self-validation checklist after step execution
      <assertion>:
        method: <data_collection_method>                    # Inspection method (e.g., "Read the last five lines of ./slurm-*.out")
        guard: <validation_rule_or_condition>               # Evaluable rule expression or natural language condition (e.g., "Must contain 'Normal termination'")

  # --- Routing and State Control (Defaults to proceeding to the sequentially next step) ---
    when:                                                   # Evaluated sequentially, stops on first match (Short-circuit evaluation)
      - condition: <trigger_condition_description>          # Trigger condition (derived from 'action' execution feedback or 'checks' self-validation results)
        evidence: <observable_evidence_source>              # Source of evidence for the judgment (e.g., "OOM appears in the log", or "User expressed dissatisfaction at the audit breakpoint and provided modification suggestions")
        response: <response>                                # Response action, see specific state definitions below
        message: <state_transition_message_or_instruction>  # Accompanying instruction or context for the state transition (e.g., troubleshooting suggestions when throwing an exception, or guiding the adjustment direction for the next task, such as "Parse and execute the user's modification suggestions provided at this breakpoint")
```

## State Machine & Routing

The `<response>` field only accepts the following five directives:

**Lifecycle Directives:**

- `SUCCESS`: Confirms completion of the current-level task, returns values, and returns execution to the upper level of the call stack.
- `FAIL`: Triggers an irreversible failure, interrupts, and destroys the current workflow instance.
- `RETRY`: Maintains the current execution stack and re-executes the current Task or Step.

**Control Flow & Exception Directives:**

- `goto(<step_id>)`: Intra-stack jump; transfers execution flow to a specified step within the current file.
- `raise(<status_string>)`: Exception bubbling; suspends a state that cannot be resolved by the current processing stack and delegates it to the parent task or human intervention.

**Specific Examples:**

```yaml
when:
    # --- Handling unmet environment conditions ---
  - condition: CUDA is not available
    evidence: torch.cuda.is_available() returned False
    response: raise(unsupported environment)
    message: This workflow heavily relies on GPU acceleration. Please inform the
      user to check the Nvidia drivers or switch to a GPU node on Slurm before 
      retrying.

    # --- Automatic retry ---
  - condition: Network timeout while fetching data
    evidence: TimeoutError in requests.get
    response: RETRY
    message: Wait for 5 seconds and increase the timeout parameter to 60s.

    # --- Early success ---
  - condition: The target file already exists and is valid
    evidence: File ./output.log size > 0 and contains 'Finished'
    response: SUCCESS
    message: Target already achieved from a previous run, skipping computation.
```
