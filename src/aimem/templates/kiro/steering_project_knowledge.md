---
inclusion: always
---

# Project Knowledge

Keep durable repository knowledge in Kiro steering files. Do not create a separate memory
directory, metadata index, proposal store, or session transcript.

## Where to record knowledge

- Update `product.md` for product purpose, users, domain terms, and behavior.
- Update `tech.md` for dependencies, commands, tooling, constraints, and validation workflows.
- Update `structure.md` for architecture, dependency direction, layout, naming, and patterns.
- Create a focused steering file when a rule needs narrower inclusion or does not fit those files.

## Maintaining knowledge

After completing work, invoke the `lesson-learning` skill when the session may contain a
validated, reusable lesson. Let the skill inspect existing guidance, avoid duplicates, and update
the appropriate native instruction or steering file. If no durable lesson emerged, make no
knowledge changes.

Preserve YAML frontmatter and existing user-authored guidance. Use Kiro's native `inclusion`,
`fileMatchPattern`, and related steering fields to scope focused rules.

Record only knowledge that is validated, reusable, likely to remain true, and specific enough
for a future coding agent to act on. Do not retain secrets, credentials, personal data,
temporary plans, task progress, unvalidated assumptions, one-off details, or transcripts.
Check existing steering first and update the owning section instead of duplicating guidance.
Current explicit user instructions take precedence over steering.