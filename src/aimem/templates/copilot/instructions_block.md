## AI Memory

This project uses **aimem** for persistent, cross-tool agent memory. Canonical memory
lives in Markdown files and is injected into your context automatically at session start.
Treat it as established project truth.

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared).
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project).
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed).

When you learn a durable fact, record it:
`{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<fact>"`.
Never store secrets, tokens, passwords, or personal data in memory. See
`.github/instructions/aimem-memory.instructions.md` and `AGENTS.md` for the full protocol.
