---
name: create-skill
description: Create new Agent Skills following the agentskills.io specification. Use when the user wants to create, scaffold, or design a new skill for AI agents. Handles SKILL.md generation, directory structure setup, and validation.
license: MIT
metadata:
  author: njzjz-bot
  version: '1.0'
---

# Create Skill

This skill helps you create new Agent Skills that follow the [agentskills.io specification](https://agentskills.io/specification).

## Quick Start

When asked to create a new skill:

1. **Gather requirements**: Ask what the skill should do
1. **Choose a name**: lowercase letters, numbers, hyphens only (e.g., `pdf-processing`, `data-analysis`)
1. **Generate the structure**: Create `SKILL.md` with proper frontmatter
1. **Add optional components**: scripts, references, assets as needed

## Directory Structure

```
skill-name/
├── SKILL.md          # Required: main skill file
├── scripts/          # Optional: executable code
├── references/       # Optional: additional documentation
└── assets/           # Optional: static resources
```

## SKILL.md Template

```markdown
---
name: your-skill-name
description: What this skill does and when to use it. Be specific and include keywords that help agents identify relevant tasks. Max 1024 characters.
license: MIT
compatibility: Optional - environment requirements if any
metadata:
  author: your-name
  version: "1.0"
allowed-tools: Optional - pre-approved tools (experimental)
---

# Skill Title

Brief introduction to the skill.

## Usage

Step-by-step instructions on how to use this skill.

## Examples

Example inputs and outputs.

## Notes

Common edge cases and tips.
```

## Field Requirements

### name (required)

- 1-64 characters
- Lowercase letters, numbers, hyphens only
- Cannot start or end with `-`
- No consecutive hyphens `--`
- Must match directory name

**Valid**: `pdf-processing`, `data-analysis`, `code-review-2`
**Invalid**: `PDF-Processing`, `-pdf`, `pdf--processing`

### description (required)

- 1-1024 characters
- Describe WHAT the skill does AND WHEN to use it
- Include specific keywords for discoverability

**Good**: "Extracts text and tables from PDF files. Use when working with PDF documents, extracting content from PDFs, or processing scanned documents."
**Poor**: "Helps with PDFs."

### license (optional)

- License name or reference to bundled license file
- Examples: `MIT`, `Apache-2.0`, `Proprietary. LICENSE.txt has complete terms`

### compatibility (optional)

- 1-500 characters
- Only include if skill has specific environment requirements
- Examples: "Requires Python 3.8+ and pandas", "Needs internet access for API calls"

### metadata (optional)

- Arbitrary key-value pairs
- Common keys: `author`, `version`, `tags`

### allowed-tools (optional, experimental)

- Space-delimited list of pre-approved tools
- Example: `Bash(git:*) Bash(jq:*) Read`

## Best Practices

### Progressive Disclosure

Design for efficient context usage:

1. **Metadata** (~100 tokens): Loaded at startup for all skills
1. **Instructions** (\<5000 tokens recommended): Loaded when skill is activated
1. **Resources**: Loaded on-demand

Keep `SKILL.md` under 500 lines. Move detailed content to `references/`.

### File Organization

- Keep `SKILL.md` focused on core instructions
- Put detailed docs in `references/REFERENCE.md`
- Put templates in `assets/`
- Put executable code in `scripts/`

### File References

Use relative paths from skill root:

```markdown
See [the reference guide](references/REFERENCE.md) for details.
Run: scripts/process.py
```

Keep references one level deep. Avoid deeply nested chains.

## Validation

After creating a skill, validate it:

```bash
# Install skills-ref if needed
npm install -g @agentskills/skills-ref

# Validate the skill
skills-ref validate ./your-skill-name
```

## Workflow Example

When asked to create a skill for X:

1. Create directory: `your-skill-name/`
1. Write `SKILL.md` with:
   - Proper frontmatter (name, description)
   - Clear instructions in Markdown body
1. Optionally add:
   - `scripts/` for helper scripts
   - `references/` for detailed docs
   - `assets/` for templates/data
1. Validate with `skills-ref validate`
1. Test the skill with an agent

## Common Patterns

### Simple Skill

Just a `SKILL.md` with instructions:

```
my-skill/
└── SKILL.md
```

### Skill with Scripts

For skills that run code:

```
my-skill/
├── SKILL.md
└── scripts/
    └── helper.py
```

### Skill with References

For detailed documentation:

```
my-skill/
├── SKILL.md
└── references/
    ├── REFERENCE.md
    └── examples.md
```

### Full-featured Skill

```
my-skill/
├── SKILL.md
├── scripts/
│   ├── setup.sh
│   └── process.py
├── references/
│   ├── API.md
│   └── FORMATS.md
└── assets/
    ├── template.json
    └── schema.json
```

## References

- [Official Specification](https://agentskills.io/specification)
- [Documentation Index](https://agentskills.io/llms.txt)
- [skills-ref Validator](https://github.com/agentskills/agentskills/tree/main/skills-ref)
