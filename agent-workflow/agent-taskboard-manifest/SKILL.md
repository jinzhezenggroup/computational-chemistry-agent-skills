---
name: agent-taskboard-manifest
description: >
  It is a specification for semantic workflows used by agents to plan, generate, formalize, summarize, and execute complex tasks, projects, experiments, and research efforts for agents, requiring explicit structure, lazy loading, scoped context, evidence-grounded routing, and human review at critical checkpoints.
  USE WHEN the user asks for a complex task, project, experiment, or research effort that needs to be carefully planned before execution.
  USE WHEN the user provides a text-based plan and wants it to be made more detailed and formalized according to this specification.
  USE WHEN the user asks to summarize ongoing or completed work into a reusable workflow manifest.
  USE WHEN the user specifies the location of an existing agent workflow and wants it loaded and executed according to the specification.
metadata:
  author: light-cyan
  version: 0.1.0
  repository: https://github.com/light-cyan/AgentTaskboardManifest
---

# Agent Workflow Specification (AgentTaskboardManifest)

## Execution Procedure

It is **mandatory** for the Agent to read `./reference/syntax_and_semantics.md` as the definitive source of truth prior to evaluating task routes, interpreting user intent, or generating any workflow artifacts.

After establishing this foundation, the Agent must determine the applicable execution route and strictly execute the corresponding standard operating procedures:

### Route 1: Planning / Generation

*Applies when building a new workflow from scratch collaboratively.*

1. **Mandatory Reading:** `./reference/plan_communication_guidelines.md`.
1. **Initial Alignment & Baseline:** Engage with the user to outline the macro-level structure. Produce the minimum baseline deliverables (`-workflow.yaml` and `!entry.task.yaml`), report the preliminary architecture to the user, and **pause execution** to await user confirmation.
1. **Mandatory Reading:** `./reference/design_guidelines.md` (Proceed only after user approval of the baseline).
1. **Iterative Refinement:** Progressively expand the workflow details and deep-level tasks through continuous user consultation. Strictly adhere to syntax and design constraints. Arbitrary fabrication of steps or dependencies is strictly prohibited.

### Route 2: Formalization / Summarization

*Applies when converting a text plan into a manifest, or abstracting completed work into a reusable workflow.*

1. **Mandatory Reading:** `./reference/design_guidelines.md`.
1. **Context Processing & Abstraction:**
   - *For text-based plans:* Logically expand the provided details. Proactively query the user regarding any ambiguous logic, missing constraints, or edge cases. Use `unknown` for unverified parameters.
   - *For summarizing executed work:* Extract and abstract hardcoded values into reusable variables. Separate run-specific instances from universal logic to ensure the resulting workflow is highly extensible, not a one-off script.
1. **Finalization:** Output the complete workflow strictly adhering to the syntax constraints. Generating unsupported operations or assuming user intent without confirmation is strictly prohibited.

### Route 3: Loading & Execution

*Applies when directed to execute an existing workflow.*

1. **Pre-flight Check:** Verify that the target workflow directory exists and is accessible. Read the `-workflow.yaml` to confirm its applicability and prerequisites against the current environment.
1. **Mandatory Reading:** `./reference/execution_guidelines.md`.
1. **Strict Execution:** Dynamically load tasks step-by-step, strictly starting from `!entry.task.yaml`. The Agent must rigidly follow the defined sequence, evaluate routing conditions based entirely on runtime evidence, and respect all defined human-in-the-loop breakpoints. Deviating from or hallucinating beyond the defined workflow path is strictly prohibited.
