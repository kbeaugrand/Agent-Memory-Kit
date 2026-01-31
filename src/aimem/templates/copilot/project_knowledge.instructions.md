---
applyTo: "**"
---

# Project Knowledge

Keep durable repository knowledge in GitHub Copilot instruction files. Do not create a separate
memory directory, metadata index, proposal store, or session transcript.

## Where to record knowledge

- Add repository-wide guidance outside the aimem-managed block in
  `.github/copilot-instructions.md`.
- Create or update a focused `.github/instructions/*.instructions.md` file when guidance applies
  only to selected paths.
- Use the `applyTo` frontmatter field to scope focused instructions to the files they govern.

## Maintaining knowledge

After completing work, invoke the `lesson-learning` skill when the session may contain a
validated, reusable lesson. Let the skill inspect existing guidance, avoid duplicates, and update
the appropriate native instruction or steering file. If no durable lesson emerged, make no
knowledge changes.

Preserve frontmatter, managed markers, and existing user-authored guidance. Never place learned
project rules inside the aimem-managed block because rerunning `aimem init` may update that block.

Record only knowledge that is validated, reusable, likely to remain true, and specific enough
for a future coding agent to act on. Do not retain secrets, credentials, personal data,
temporary plans, task progress, unvalidated assumptions, one-off details, or transcripts.
Check existing instructions first and update the owning section instead of duplicating guidance.
Current explicit user instructions take precedence over repository instructions.