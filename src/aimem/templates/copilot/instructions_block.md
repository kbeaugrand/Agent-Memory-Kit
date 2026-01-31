## AI Memory

This project uses **aimem** for persistent, cross-tool agent memory. Canonical memory
lives in Markdown files and is injected into your context automatically at session start.
Treat memory as durable, validated project context, but follow the current explicit user
request first and surface unresolved conflicts.

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared).
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project).
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed).

Recognize reusable repository problem-solving lessons as they emerge. A Stop hook invokes
the `lesson-learning` skill for one review turn; hook scripts do not parse transcripts or
author memory themselves. Automatically add or update concise project memory for a
high-confidence lesson supported by an explicit user correction or decision, repeated
confirmed behavior, a successful check, or strong repository evidence, after checking for
duplicates and conflicts. When the lesson is also a coding rule, update an appropriate
user-owned instruction or steering file, never an aimem-managed artifact. Use
`memory_propose` followed by `memory_approve`, and report the activation in your final
response. Require explicit approval for user memory, personal preferences, uncertain claims,
and deprecations or deletions. Use `memory_search`, `memory_get`, `memory_context`,
`memory_handoff`, and `memory_conflicts` to inspect and curate memory.
If MCP is unavailable, fall back to:
`{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<fact>"`.
Never store secrets, tokens, passwords, personal data, temporary progress, unvalidated
assumptions, or full conversation transcripts in memory. See
`.github/instructions/aimem-memory.instructions.md` and `AGENTS.md` for the full protocol.
