<!-- AIMEM:BEGIN (managed by aimem — do not edit inside this block; run `aimem init` to update) -->
## AI Memory

This project uses **aimem** for persistent, cross-tool agent memory. Canonical memory
lives in Markdown files and is injected into your context automatically at session start.
Treat memory as durable, validated project context, but follow the current explicit user
request first and surface unresolved conflicts.

- **Project memory** — `.aimem/memory/project.md` (committed, team-shared).
- **User memory** — `~/.aimem/memory/user.md` (personal, cross-project).
- **Session memory** — `.aimem/memory/session/current.md` (ephemeral, not committed).

Recognize reusable repository problem-solving lessons as they emerge and review the session
before your final response. When a lesson is validated by repository evidence or a
successful check, automatically add or update concise project memory after checking for
duplicates and conflicts. Use `memory_propose` followed by `memory_approve`, and report the
activation in your final response; hooks manage lifecycle and security but do not author
memory. Require explicit approval for user memory, inferred preferences, uncertain claims,
and deprecations or deletions. Use `memory_search`, `memory_get`, `memory_context`,
`memory_handoff`, and `memory_conflicts` to inspect and curate memory.
If MCP is unavailable, fall back to:
`python3 .aimem/hooks/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<fact>"`.
Never store secrets, tokens, passwords, personal data, temporary progress, unvalidated
assumptions, or full conversation transcripts in memory. See
`.github/instructions/aimem-memory.instructions.md` and `AGENTS.md` for the full protocol.
<!-- AIMEM:END -->
