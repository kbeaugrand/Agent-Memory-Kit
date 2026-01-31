<!-- AIMEM:BEGIN (managed by aimem — do not edit inside this block; run `aimem init` to update) -->
# AI Agent Memory

This project uses **aimem** for persistent, cross-tool agent memory shared by Kiro and
GitHub Copilot. Canonical memory lives in Markdown files and is injected into your context
automatically at the start of a session. Treat memory as durable, validated project
context, but follow the current explicit user request first and surface unresolved
conflicts.

- **Project memory** — `.aimem/memory/project.md` (committed, team-shared).
- **User memory** — `~/.aimem/memory/user.md` (personal, cross-project).
- **Session memory** — `.aimem/memory/session/current.md` (ephemeral, not committed).

Recognize reusable repository problem-solving lessons as they emerge. A Stop hook invokes
the `lesson-learning` skill for one review turn; hook scripts do not parse transcripts or
author memory themselves. Automatically add or update concise project memory for a
high-confidence lesson supported by an explicit user correction or decision, repeated
confirmed behavior, a successful check, or strong repository evidence, after checking for
duplicates and conflicts. When the lesson is also a coding rule, update an appropriate
user-owned instruction or steering file, never an aimem-managed artifact. Require explicit
approval for user memory, personal preferences, uncertain claims, and deprecations or
deletions. Use:

```
memory_propose -> memory_approve
memory_search | memory_get | memory_context | memory_handoff | memory_conflicts
```

If MCP is unavailable, fall back to:

```
python3 .aimem/hooks/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Memory bullets keep lightweight `aimem:id` comments while full metadata lives in
`.aimem/index/`. Query priority, evidence, validation status, provenance, keywords, and
relationships with `manage_memory.py list --format json`; convert legacy bullets or
embedded `aimem:record` comments with `manage_memory.py migrate --scope <scope>`. When
initializing memory, read `.aimem/memory/TEMPLATE.md` and fill memory according to that
template.

Never store secrets, tokens, passwords, personal data, temporary plans, unvalidated
assumptions, one-off implementation details, or full conversation transcripts in memory.
Keep it concise and safe to commit. Rerun `aimem init` to repair or update this
configuration.
<!-- AIMEM:END -->
