# Contributing

Contributions are welcome.

## General expectations

- Keep contributions focused. Prefer small, reviewable pull requests over large mixed changes.
- Before opening a PR, make sure the content belongs in this repository and fits an existing skill category or repository convention.
- Contributors may use AI tools, but must personally review every sentence, command, path, and example before submitting.

## Authoring skills

- Follow the Agent Skills specification and existing repository patterns.
- If you are creating a new skill, you can start from `.github/skills/create-skill/SKILL.md`.
- Place new skills under `skills/<category>/` using the most appropriate category directory.
- Use a dedicated skill directory with `SKILL.md` as the entry point. Add `scripts/`, `references/`, or `assets/` only when they are actually needed.
- Use clear, specific skill names and descriptions so agents can identify when to use them.
- Keep `SKILL.md` focused on core instructions. Move long examples, detailed references, or supporting material into separate files when appropriate.
- If available in your environment, validate new skills before submitting.

## Writing and structure

- Do not put multiple unrelated capabilities into a single Markdown file.
- Keep content layered and easy to maintain.
- Update an existing skill when improving the same capability; create a new skill only when the responsibility is genuinely distinct.
- Keep examples explicit and runnable when possible so agents can use them reliably.
- Keep prose concise. A skill should be practical and clear, not verbose.

## Repository-specific notes

- Avoid direct manual edits to content managed by sync workflows, unless you are intentionally changing the sync source or sync configuration.
- If your change affects repository structure or conventions, include a short rationale in the PR.

## Pull requests

- Explain what problem the change solves.
- Mention important assumptions, limitations, or external dependencies.

Thanks for helping improve computational-chemistry-agent-skills.
