## Project Knowledge

This repository keeps durable coding-agent knowledge in native GitHub Copilot instruction files.
Store repository-wide rules outside this managed block in `.github/copilot-instructions.md`, and
store path-specific rules in `.github/instructions/*.instructions.md` with appropriate `applyTo`
frontmatter.

Use the `lesson-learning` skill after completed work when a validated, reusable lesson may have
emerged. The skill reviews the work, avoids duplicates, and updates the appropriate native
instruction or steering file. If no durable lesson emerged, it makes no changes.

Retain only validated, reusable repository knowledge. Preserve existing guidance, avoid
duplicates, never store secrets or transient task state, and follow current explicit user
instructions when they conflict with repository guidance.