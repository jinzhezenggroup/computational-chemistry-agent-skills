# Generation Guidelines

This guide establishes the structural standards and design principles that must be followed when constructing workflow topologies, defining I/O contracts, and authoring semantic actions.

## Hierarchical Depth and Separation of Duties

The generated workflow topology must be presented as a **Tree-structured Orchestration**. Constructing flat task flows that lack structural depth is strictly prohibited.

- **Vertical Separation of Concerns:** The hierarchical level of a node must strictly correspond to the abstraction level of its responsibilities. Nodes closer to the top level (e.g., `!entry.task.yaml`) should focus on macro-planning, state transitions, exception handling, and routing. Nodes closer to the leaves (deep `*.task.yaml`) should focus on specific environment interactions, data processing, and atomic execution.
- **No Redundant Nesting:** Decoupling logic into an independent subtask is only permitted if a logic block contains multiple steps, complex internal state transitions, or possesses high reuse value. If a function can be completed via a single `action` within the current task (e.g., executing a single Shell command or a one-time API request), creating a separate `.task.yaml` is strictly forbidden to prevent call-stack bloat caused by over-engineering.

## On-Demand Declaration and Scope Isolation

When designing I/O contracts for a workflow, the visibility boundaries and lifecycles of parameters must be strictly controlled to ensure each task node declares and maintains only the minimum context necessary for its execution.

- **Parameter Subordination and Encapsulation:** Adhere to the **Principle of Least Knowledge**. A parent task's `inputs` and `outputs` are only permitted to declare **core orchestration parameters** essential for current-level routing, conditional logic, and upstream/downstream handshakes.
- **Prohibit Top-Level Penetration:** It is strictly forbidden to exhaustively declare low-level execution parameters required by deep subtasks within the interface contracts of top-level or high-level tasks. Details required for deep dependencies must be pushed down to the specific nodes that actually consume them. If a low-level node cannot obtain a parameter at initialization, it should be described as "unknown" and dynamically obtained through `action` in the local execution flow at that level.

## Semantic Action Descriptions

The authoring of `action` and `guard` fields in `checks` should favor describing "intent" and "acceptance criteria" rather than being constrained by the rigid syntax of a specific programming language. **KEY PRINCIPLES: When planning specific actions, priority must be given to scheduling Agent Skills; do not manually code low-level scripts to execute tasks or generate structured data files that should be produced by specialized tools.** Trust that the downstream Agent can accurately translate natural language instructions into actual environmental operations at runtime.

## Managing Unknowns

During the generation phase, it is strictly forbidden to make any form of static assumption or forge outputs based on guesswork. When facing uncertainty, unknown states must be deferred to the **Runtime** for dynamic resolution:

- **Parameter & Data Absence:**
  - If variables lack environmental priors or user input, do not fabricate default values.
  - Describe them as **"unknown"** within the natural language descriptions of the I/O contract.
  - Design active collection mechanisms via `action` in the associated `<step_object>` (e.g., `action: "Inquire user for the required credentials..."` or `action: "Run environment probe script to determine..."`).
- **Execution Logic Ambiguity:**
  - If there is vague understanding regarding the specific toolchain, command syntax, or low-level operational flow needed to achieve a goal, do not force or fabricate specific execution steps.
  - Downgrade that segment to an "exploratory node," explicitly express the unknown in the `action`, and rely on external retrieval or human intervention at runtime to resolve the logic (e.g., `action: "Search the official documentation to find the correct command for..."` or `action: "Inquire user about the preferred method/tool to process this data."`).

## Human-in-the-Loop & Breakpoint Design

When planning workflows, humans must be treated as critical audit nodes within the execution flow. Agents must proactively design blocking **audit breakpoints** in high-value or high-risk scenarios (e.g., by initiating an inquiry via **`action: "Request user to review the current work..."`** and waiting for confirmation). Silent execution is strictly prohibited in the following cases:

- **Before High-Risk & Irreversible Actions:** A `<step_object>` requesting user authorization and confirmation must be inserted before executing critical actions such as batch deleting files, overwriting core data, submitting resource-intensive compute tasks, or calling metered APIs.
- **Milestone Validation:** After the workflow completes complex logical reasoning, code generation, or data transformation, and before proceeding to downstream consumption, breakpoints should be designed to present intermediate artifacts or generated products to the user for accuracy review.
- **Strategic Branching:** When task progression faces multiple parallel viable strategies that cannot be automatically decided by preset rules, options should be listed in the `action`, delegating the routing decision to the user (e.g., `"Inquire user to select the preferred processing method: [Option A, Option B]"`).

## Robust Routing

Design comprehensive `when` branches for every critical `<step_object>`. At least three states must be considered to generate appropriate routing responses:

1. **Expected Success:** (`goto` next step or `SUCCESS`).
1. **Recoverable Exception or Human Intervention:** (Trigger `RETRY` or transition to a corrective `<step_id>` based on runtime errors or **feedback/modifications provided by the user at an audit breakpoint**).
1. **Unrecoverable Exception:** (Bubble up via `raise` or trigger a global `FAIL`).

## Case Studies
