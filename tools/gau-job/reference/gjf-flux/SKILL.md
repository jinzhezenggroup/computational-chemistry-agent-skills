---
name: gjf-flux
description: Assemble and extract Gaussian .gjf input file sections (directives, route, title, molecule blocks, appendices) and build single- or multi-step Link1 jobs from modular component files. Use when generating, refactoring, templating, or scripting Gaussian job files.
compatibility: Requires `uv` installed and available in PATH.
metadata:
  author: light-cyan
  version: 0.1.0
  repository: https://github.com/light-cyan/gjf-flux
---

# gjf-flux (Gaussian Job File Assembly & Extraction)

`gjf-flux` is a command-line workflow for **modular Gaussian `.gjf` files**:

- **Extract** a specific section from an existing `.gjf` (including Link1 multi-step jobs).
- **Assemble** directives/route/molecule/appendix blocks into a complete `.gjf`, or merge multiple tasks into a Link1 job.

## When to use

Use this skill when you need to:

- Reuse parts of Gaussian inputs across many calculations (e.g., route lines, molecule blocks, basis/constraints appendices).
- Programmatically build `.gjf` jobs from smaller files (fragments, templates, parameterized directives).
- Inspect/compare `.gjf` files by extracting specific sections.

## Assumptions / Parsing model (important)

`gjf-flux` assumes a **standard Gaussian input layout**:

- Link1 steps are separated by a blank line, then `--Link1--`, then a newline.
- Within each Link1 step, blocks are separated by blank lines.
- The **route section** begins at the first line starting with `#` and continues through subsequent lines.
- A **molecule block** is detected when the first line of a block looks like paired integers
  (e.g., `0 1` or `0 1 0 1 0 1`), representing charge/multiplicity pairs.

If a `.gjf` deviates from these conventions, extraction may fail or misclassify blocks.

## Inputs you should request from the user

When helping a user, clarify:

1. Target action: **extract** vs **assemble**.
1. File paths:
   - Existing `.gjf` to read, or component files to assemble.
1. For Link1 jobs:
   - Which step to extract (`job_index`, 0-based), or how many steps to assemble.
1. Molecule content:
   - Total charge/multiplicity, fragment charge/multiplicity (if using fragments), coordinate format.
1. Appendices:
   - Whether there are basis sets, ECPs, ModRedundant constraints, etc.

## Core commands (cheat sheet)

### 1) Extract a section from a `.gjf`

```bash
uvx gjf-flux extract <section_name> <FILE.gjf> [--job_index N]
```

Where `<section_name>` is one of:

- `directives`
- `route`
- `title`
- `molecule` or `molecule-<idx>`
- `appendix` or `appendix-<idx>`

Notes:

- `<idx>` is **0-based**.
- `--job_index` selects the Link1 step (**0-based**, default `0`).

Examples:

```bash
# Extract the route line from the first Link1 step
uvx gjf-flux extract route input.gjf

# Extract the second molecule block from step 0
uvx gjf-flux extract molecule-1 input.gjf

# Extract the first appendix block from Link1 step 2
uvx gjf-flux extract appendix-0 input.gjf --job_index 2
```

### 2) Assemble directives (Link0 commands)

```bash
uvx gjf-flux assemble directives --chk FILE --mem SIZE --nprocshared N
```

This command accepts key/value pairs in the form `--key value`.

Examples:

```bash
uvx gjf-flux assemble directives --chk job.chk --mem 16GB --nprocshared 16
```

Tip: redirect to a file for later composition:

```bash
uvx gjf-flux assemble directives --chk job.chk --mem 16GB --nprocshared 16 > directives.txt
```

### 3) Assemble the route section (`#` line)

```bash
uvx gjf-flux assemble route [-l p|n|t|""] <keywords...>
```

Examples:

```bash
#p Opt B3LYP/6-31G(d)
uvx gjf-flux assemble route -l p Opt B3LYP/6-31G(d)

# Use quotes for keywords with parentheses
uvx gjf-flux assemble route -l p "Opt(MaxCycle=100)" "Freq"
```

Tip:

```bash
uvx gjf-flux assemble route -l p "Opt(MaxCycle=100)" "Freq" > route.txt
```

### 4) Merge molecule fragments into one molecule block

```bash
uvx gjf-flux assemble molecules <frag1.txt> <frag2.txt> ... [--as-fragment] [--charge INT] [--multi INT]
```

Each fragment file must follow this format:

- Line 1: `charge multiplicity` (e.g., `0 1`)
- Following lines: atomic coordinates (Gaussian-style)

Modes:

- Default: merges into a **single** molecule block.
- `--as-fragment`: assigns `Fragment=1,2,...` tags and expands the charge/multiplicity header.

Examples:

```bash
# Merge two fragments into a single molecule block
uvx gjf-flux assemble molecules fragA.txt fragB.txt > molecule.txt

# Merge as fragments, overriding total charge/multiplicity
uvx gjf-flux assemble molecules fragA.txt fragB.txt --as-fragment --charge 0 --multi 1 > molecule.txt
```

### 5) Assemble appendices

```bash
uvx gjf-flux assemble appendices <app1.txt> <app2.txt> ...
```

Examples:

```bash
uvx gjf-flux assemble appendices basis.txt modredundant.txt > appendix.txt
```

### 6) Assemble a complete single-step `.gjf`

```bash
uvx gjf-flux assemble job \
    --directives directives.txt \
    --route route.txt \
    --title "Your title" \
    --molecule molecule.txt [molecule2.txt ...] \
    [--appendices appendix.txt ...]
```

### 7) Merge multiple tasks into a Link1 multi-step job

```bash
uvx gjf-flux assemble tasks step1.gjf step2.gjf [step3.gjf ...] > link1.gjf
```

## End-to-end example (one-liners with command substitution)

This example shows a **single-step** job assembled from:

- directives: produced directly from CLI flags
- route: produced inline from `assemble route`
- molecule: extracted from an existing `.gjf`, then re-merged (optionally overriding multiplicity)
- appendices: extracted from other `.gjf` files and concatenated

> Note: This uses bash/zsh process substitution (`<(...)`). If you are on a shell that does not support it, redirect each block into a file first.

```bash
# 1) Build directives to a file (recommended; easier to audit)
uvx gjf-flux assemble directives --chk job.chk --mem 16GB --nprocshared 16 > directives.txt

# 2) Assemble a full .gjf using inline-generated route/molecule/appendix blocks
uvx gjf-flux assemble job \
    --directives directives.txt \
    --route <(uvx gjf-flux assemble route -l p "Opt(MaxCycle=100)" "Freq" B3LYP/6-31G(d)) \
    --title "Opt+Freq from extracted building blocks" \
    --molecule <( \
        gjf-flux assemble molecules \
        <(uvx gjf-flux extract molecule-0 reactant.gjf) \
        fragment_extra.xyz \
        --multi 1 \
    ) \
    --appendices \
    <(uvx gjf-flux extract appendix-1 reactant.gjf) \
    <(uvx gjf-flux extract appendix-0 reference.gjf) \
    app_manual.txt \
    > job.gjf
```

Variants:

- If you only want to **reuse** an extracted molecule block verbatim (no merge), pass:
  - `--molecule <(uvx gjf-flux extract molecule-0 input.gjf)`
- If you are assembling a **Link1** workflow, build each step as its own `.gjf` and then:
  - `uvx gjf-flux assemble tasks step1.gjf step2.gjf > link1.gjf`

## Recommended workflow (practical)

1. Create/derive component blocks:
   - `directives.txt` (from `assemble directives` or manual)
   - `route.txt` (from `assemble route`)
   - `molecule.txt` (from `assemble molecules` or extracted from a prior `.gjf`)
   - `appendix.txt` (optional)
1. Assemble a complete job via `assemble job`.
1. If you have multiple steps, build each step as a `.gjf` and then merge using `assemble tasks`.
1. Verify by extracting critical sections from the final output.

## Common pitfalls

- **Wrong indexing**: `job_index`, `molecule-<idx>`, and `appendix-<idx>` are all **0-based**.
- **Non-standard `.gjf` formatting**: unusual blank-line structure can break parsing.
- **Fragment files must start with `charge multiplicity`**: otherwise molecule merge will fail.
- **Keyword quoting**: route keywords with parentheses should be quoted in the shell.

## Notes for agents

- Prefer asking the user for a concrete example `.gjf` if parsing fails.
- When assembling, keep each component file small and purpose-specific; it makes debugging far easier.
- If the user wants a repeatable pipeline, suggest storing reusable components (route templates, basis set appendices, fragment libraries) in version control.
