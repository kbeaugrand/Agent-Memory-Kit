---
inclusion: always
---

# AI Memory Protocol (managed by aimem)

This project uses a persistent, cross-tool memory system. Canonical memory lives in plain
Markdown files and is injected into your context automatically at the start of a session
and on each prompt. Treat injected memory as established project truth.

## Memory scopes

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared): conventions,
  architecture, build/test/run commands, gotchas, and domain glossary.
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project): individual preferences.
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed): working notes for
  the current task.

## Recording memory

When you learn a durable fact — a decision, convention, command, or gotcha — record it:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Route it correctly: **project** for team-shared repo facts, **user** for personal
preferences, **session** for ephemeral notes. Prefer updating an existing entry over
adding a duplicate. If a user instruction conflicts with memory, follow the user and then
update memory.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` guard
blocks obvious secret writes, and a post-save hook normalizes and de-duplicates memory —
but you are the first line of defense. Keep memory safe to commit and share.

## Curation

Keep memory concise. When it grows or drifts, switch to the **memory-curator** agent to
consolidate, merge duplicates, and remove stale entries.
