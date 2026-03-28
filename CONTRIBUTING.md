# Contributing

Contributions are welcome.

## General expectations

- Keep contributions focused. Prefer small, reviewable pull requests over large mixed changes.
- Before opening a PR, make sure the content belongs in this repository and follows the Agent Skills format.
- Contributors may use AI tools, but must personally review every sentence, command, path, and example before submitting.

## Writing and structure

- Follow the Agent Skills specification and existing repository patterns.
- If you are authoring a new skill, you may use `.github/skills/create-skill` when available to help scaffold or validate the structure.
- Do not put multiple unrelated capabilities into a single Markdown file.
- Keep content layered and easy to maintain. Use separate files or subdirectories when examples, assets, references, or helper scripts would otherwise make one file too large.
- Keep prose concise. A skill should be practical and clear, not verbose.

## Repository-specific notes

- Update existing skills when improving the same capability; create a new skill only when the responsibility is genuinely distinct.
- When relevant, keep examples runnable and explicit so agents can use them reliably.
- Avoid direct manual edits to content managed by sync workflows, unless you are intentionally changing the sync source or sync configuration.

## Pull requests

- Explain what problem the change solves.
- Mention any important assumptions, limitations, or external dependencies.
- If your PR changes repository structure or conventions, include a short rationale.

Thanks for helping improve computational-chemistry-agent-skills.
