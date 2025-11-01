---
applyTo: "**"
---

# AI Memory Protocol (managed by aimem)

This project uses a persistent, cross-tool memory system. Canonical memory lives in plain
Markdown files and is injected into your context automatically at the start of a session.
Treat injected memory as established project truth; if a user instruction conflicts with
memory, follow the user and then update memory.

## Memory scopes

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared): conventions,
  architecture, build/test/run commands, gotchas, and domain glossary.
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project): individual preferences.
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed): working notes for
  the current task.

## Recording memory

When you learn a durable fact — a decision, convention, command, or gotcha — record it to
the correct scope (project for team-shared repo facts, user for personal preferences,
session for ephemeral notes):

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Prefer updating an existing entry over adding a duplicate.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` hook
blocks obvious secret writes, and a `PostToolUse` hook normalizes and de-duplicates memory
files. Keep memory safe to commit and share.

## Curation

Keep memory concise. When it grows or drifts, switch to the **memory-curator** agent to
consolidate, merge duplicates, and remove stale entries.
