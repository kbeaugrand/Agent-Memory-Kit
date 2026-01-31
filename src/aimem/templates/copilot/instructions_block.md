## Project Knowledge

This repository keeps durable coding-agent knowledge in native GitHub Copilot instruction files.
Store repository-wide rules outside this managed block in `.github/copilot-instructions.md`, and
store path-specific rules in `.github/instructions/*.instructions.md` with appropriate `applyTo`
frontmatter.

Retain only validated, reusable repository knowledge. Preserve existing guidance, avoid
duplicates, never store secrets or transient task state, and follow current explicit user
instructions when they conflict with repository guidance.

After completing work, use the `lesson-learning` skill to record validated, reusable lessons in
the appropriate GitHub Copilot custom instruction or Kiro steering file. If no durable lesson
emerged, make no knowledge changes.
