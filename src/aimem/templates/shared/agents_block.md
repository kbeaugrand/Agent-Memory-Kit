# AI Agent Memory

This project uses **aimem** for persistent, cross-tool agent memory shared by Kiro and
GitHub Copilot. Canonical memory lives in Markdown files and is injected into your context
automatically at the start of a session. Treat memory as durable, validated project
context, but follow the current explicit user request first and surface unresolved
conflicts.

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared).
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project).
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed).

Never activate memory silently. Recognize durable lessons as they emerge during work
(user corrections or stated rules, confirmed fixes, verified commands, validated decisions)
and initiate the proposal yourself; hooks only manage the memory lifecycle and never author
memory. When durable knowledge appears, present a memory candidate with scope, action,
target, reason, and exact proposed content. Approval required before activation.
Only after explicit approval, or when the user directly asks you to record memory, use:

```
memory_propose -> memory_approve
memory_search | memory_get | memory_context | memory_handoff | memory_conflicts
```

If MCP is unavailable, fall back to:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Memory bullets keep lightweight `aimem:id` comments while full metadata lives in
`.aimem/index/`. Query priority, evidence, validation status, provenance, keywords, and
relationships with `manage_memory.py list --format json`; convert legacy bullets or
embedded `aimem:record` comments with `manage_memory.py migrate --scope <scope>`. When
initializing memory, read `{{MEMORY_TEMPLATE}}` and fill memory according to that
template.

Never store secrets, tokens, passwords, personal data, temporary plans, unvalidated
assumptions, one-off implementation details, or full conversation transcripts in memory.
Keep it concise and safe to commit. Rerun `aimem init` to repair or update this
configuration.
