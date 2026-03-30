# Execution Guidelines

This guide defines the specific behavioral logic for the Agent during runtime regarding configuration loading, variable scope handling, execution state evaluation, and exception intervention triggering.

## Lazy Loading Strategy

- **Initialization:** Upon startup, the Agent must *only* read `-workflow.yaml` to load the global context and read `!entry.task.yaml` to establish the main execution stack.
- **On-Demand Loading:** Only when the execution flow reaches a `<step_object>` that references a sub-task (e.g., `action: "Execute sub-task ./xxx.task.yaml"`), is the Agent permitted to dynamically load the target YAML file into the context.

## Variables Passing & Scope

- **Context Inheritance:** When a sub-task is invoked, it automatically inherits the global context (`global_conventions`) and the `inputs` of the parent task.
- **Context Consolidation:** When parameters described as "unknown" are dynamically resolved or new `<artifact>`s are generated via an `action`, the Agent should explicitly organize and record their states in its working memory. Synchronize the acquired exact values, physical paths, or entity characteristics into the context of the current execution scope to ensure downstream `checks` self-validation and `when` state transitions have an accurate data baseline.

## Execution Flow & State Transition Logic

- **Prerequisite Interception:** Upon entering any `*.task.yaml` node, the Agent must prioritize validating `prerequisites`. If collected evidence indicates conditions are unmet, it must immediately suspend or throw an exception; blindly entering the core `steps` sequence is strictly prohibited.
- **Evidence-Grounded Routing:** The routing of a `<step_object>` strongly depends on rigorous verification of actual runtime feedback. After step execution, the Agent must examine the actual generated context (e.g., stdout logs, API responses, user inputs, or self-validation results). When routing based on the `when` array, the `condition` (trigger condition) and `evidence` (basis for judgment) work collaboratively: The Agent must use the concrete observable features declared in `evidence` as a validation baseline to extract factual support from actual execution results. Only when concrete facts matching the `evidence` are retrieved from the actual context, thereby proving the `condition` is established, is that routing branch considered a match, subsequently triggering the corresponding state machine directives.
- Matching Strategy Supplement:
  - The evaluation of the `when` array follows the *Short-circuit evaluation* rule. Compare top-down one by one; hitting the first condition with factual support immediately triggers the state transition and strictly ignores all subsequent branches in the array.
  - If the actual runtime feedback of the current `<step_object>` fails to provide the conclusive evidence required by any `evidence` in the `when` list (or if the current step does not explicitly declare a `when` array), default to continuing execution with the next `<step_object>` in the list.

## Exception Bubbling & Human Fallback

When a `<step_object>` triggers `raise(<status_string>)`, it follows these state transition and reporting rules:

1. **Automatic Flow Interruption:** Stop all automated attempts of the current sub-task to prevent error cascading and resource waste.
1. **State Bubbling and Cascading Capture:** State information is bubbled up to the `<step_object>` of the parent `*.task.yaml` that invoked this sub-task. The parent task's `when` list should attempt to match this `status_string` to execute fallback or retry logic. If not captured, the exception will continue to bubble up the call stack.
1. **Human-in-the-loop Fallback:** If the exception bubbles up to the top-level `!entry.task.yaml` and still does not match any preset routing, or directly triggers a global `FAIL` state, the Agent must strictly execute the following terminal actions:
   - Immediately report the issue to the user, outputting a formatted exception report (including the node ID throwing the exception, the `status_string`, and specific `message` evidence) to seek assistance.
   - Wait for explicit user instructions (e.g., supplement missing credentials, modify environment configurations, instruct a retry, or manually terminate) before deciding on subsequent behavior.
