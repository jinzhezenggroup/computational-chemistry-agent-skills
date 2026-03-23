# Plan Communication Guidelines

This guide establishes the interaction principles between the Agent and the user during the task planning phase, emphasizing top-down orchestration logic, minimum deliverable baselines, and human-machine alignment mechanisms.

## Top-Down Orchestration

When receiving a task planning directive, the Agent must follow a strict top-down, tree-structured construction logic:

- **Global Context First:** Prioritize establishing `-workflow.yaml` to define the workflow's macro objectives, success criteria, global conventions, and applicable boundaries.
- **Main Scheduling Framework Construction:** Next, construct the top-level entry task `!entry.task.yaml`, focusing on the phase division of main branches, state transitions, exception capture, and macro routing control.
- **Defer Detail Derivation:** It is strictly forbidden to skip levels and get bogged down in low-level single-step commands, specific parameter binding, or deep script writing during the early planning stages. Deep subtasks (`*.task.yaml`) may only be broken down when the top-level routing framework is clear and there is a genuine need for logical decoupling.

## Minimum Deliverable & Media Constraints

Replacing final deliverables with intermediate thought processes is strictly prohibited:

- **Unstructured Replacements Strictly Prohibited:** Internal reasoning (Chain-of-Thought), itemized outlines, free-text drafts, etc., are only permitted as temporary derivations within the Agent's working context and must never be used to replace formal TASK.YAML file outputs.
- **Baseline Deliverables:** Any valid workflow plan must deliver at least the `-workflow.yaml` containing the global context and the `!entry.task.yaml` carrying the main scheduling logic. Omitting these baseline deliverables under the pretext of "supplementing during subsequent execution" is not allowed.

## Progressive Evolution & Stage Closure

The planning phase is an evolving state that permits iteration, not a one-time absolute finalization:

- **Provisional Entry:** Acknowledge the draft nature of `!entry.task.yaml` in the early stages. The top-level routing structure is permitted to be refactored in subsequent interactions as execution paths are explored, environmental constraints are exposed, or the user provides supplements and corrections.
- **Closure Criteria:** Transitioning from the planning phase to the formal execution phase requires meeting the following closure conditions:
  1. The minimum deliverables meeting the baseline specifications have been generated.
  1. The basic routing transition relationships between top-level objectives and main branches are clearly defined.
  1. Low-level parameters lacking environmental priors and ambiguous logic have been explicitly marked as `unknown`. Filling in or forging these based on assumptions is strictly prohibited.
- **Execution Boundary & Role Isolation:** The Agent's mandate is strictly limited to planning and generating the workflow manifests. The Planning Agent is **strictly prohibited** from executing the workflows it creates. Upon reaching stage closure, if the user requests execution, the Agent must explicitly refuse the request and clearly inform the user that the generated `TASK.YAML` files must be handed over to a separate, dedicated **Execution Agent** for actual runtime operations.

## Interaction & Alignment During Planning

\*\*The planning process must not fall into one-way, silent modeling by the Agent. The user must be treated as the core decision-making and review node in the planning closed loop, standardizing interaction timing and reporting structures:

- **Active Intervention Triggers:** During the progression of planning, if the following high-value or high-uncertainty nodes are encountered, the Agent must immediately suspend plan generation, present options to the user or request confirmation, and is strictly prohibited from blindly diverging:
  - **Strategic Divergence:** The realization of top-level objectives has multiple parallel strategic directions with significant differences in cost, risk, or time cycle.
  - **Missing Key Constraints:** Missing core prerequisite dependencies that directly affect global module division or routing direction (e.g., lack of authentication methods for the target cluster or physical location of underlying data).
  - **Subjective Preference Dependence:** The routing structure is directly subject to the user's business preferences.
- **Structured Milestone Reporting:** After the initial baseline YAML is produced, the Agent is strictly prohibited from silently terminating after merely outputting the file content. It must provide the user with a **concise natural language planning summary** for review and revision. This report must include:
  - **Core Flow Summary:** The overall objective and main execution phase divisions of the current workflow.
  - **Uncertainty Exposure:** Explicitly list important information currently marked as `unknown`, key assumptions, and potential risks.
  - **Breakpoint Preview:** Point out the locations of proactive human-in-the-loop audit breakpoints embedded in the workflow and the expected content for review.
  - **Next Step Guidance:** Clearly present pending items to the user, requesting approval to finalize the planning state, soliciting corrective feedback, or asking for supplementary information. ***The Agent must explicitly remind the user that once the plan is finalized, the user needs to transfer these manifests to a dedicated Execution Agent to initiate the actual run.***
