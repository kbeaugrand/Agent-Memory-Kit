# AI Agent Memory

This project uses **aimem** for persistent, cross-tool agent memory shared by Kiro and
GitHub Copilot. Canonical memory lives in Markdown files and is injected into your context
automatically at the start of a session. Treat it as established project truth.

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared).
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project).
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed).

When you learn a durable fact (a decision, convention, command, or gotcha), record it to
the correct scope:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Never store secrets, tokens, passwords, or personal data in memory. Keep it concise and
safe to commit. Rerun `aimem init` to repair or update this configuration.
