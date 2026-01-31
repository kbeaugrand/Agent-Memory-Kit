<!-- AIMEM:BEGIN (managed by aimem — do not edit inside this block; run `aimem init` to update) -->
## AI Memory

This project uses **aimem** for persistent, cross-tool agent memory. Canonical memory
lives in Markdown files and is injected into your context automatically at session start.
Treat memory as durable, validated project context, but follow the current explicit user
request first and surface unresolved conflicts.

- **Project memory** — `.aimem/memory/project.md` (committed, team-shared).
- **User memory** — `~/.aimem/memory/user.md` (personal, cross-project).
- **Session memory** — `.aimem/memory/session/current.md` (ephemeral, not committed).

Never activate memory silently. Recognize durable lessons as they emerge during work
(user corrections or stated rules, confirmed fixes, verified commands, validated decisions)
and initiate the proposal yourself; hooks only manage the memory lifecycle and never author
memory. When durable knowledge appears, present a memory candidate with scope, action,
target, reason, and exact proposed content. Approval required before activation.
Only after explicit approval, or when the user directly asks you to record memory, use:
`memory_propose` followed by `memory_approve`. Use `memory_search`, `memory_get`,
`memory_context`, `memory_handoff`, and `memory_conflicts` to inspect and curate memory.
If MCP is unavailable, fall back to:
`python3 .aimem/hooks/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<fact>"`.
Never store secrets, tokens, passwords, or personal data in memory. See
`.github/instructions/aimem-memory.instructions.md` and `AGENTS.md` for the full protocol.
<!-- AIMEM:END -->
