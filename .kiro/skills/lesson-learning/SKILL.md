---
name: lesson-learning
description: Extract durable lessons from a completed coding session or agent turn, update project memory, and create or update coding instructions or Kiro steering when the lessons establish reusable coding rules.
user-invocable: false
---

# Lesson Learning

Review the completed conversation in the current context. Do not read, copy, summarize, or
persist a hook transcript file.

## Procedure

1. Identify only durable, reusable lessons. High-confidence evidence includes an explicit
   user correction or decision, repeated confirmed behavior, a successful validation, or
   strong consistency with repository evidence.
2. Search active memory and existing instructions or steering for duplicates and conflicts.
   Prefer updating an existing entry over adding another one.
3. Record high-confidence project lessons through the aimem MCP tools when available:
   inspect first, call `memory_propose`, then call `memory_approve`. If MCP is unavailable,
   use `python3 .aimem/hooks/record_memory.py` with evidence, validation status,
   source, keywords, and confidence metadata.
4. Decide whether the lesson is also a prescriptive coding rule. If it is, update the most
   appropriate existing user-owned Copilot instruction or Kiro steering file. Create a
   focused file only when no existing owner fits. Use narrow `applyTo` globs or file-match
   metadata for scoped rules and global inclusion only for genuinely global rules.
5. Make minimal edits and preserve unrelated guidance. If no durable lesson emerged, do
   nothing.

## Boundaries

- Never edit aimem-managed files, including `.aimem/hooks/`,
  `.github/instructions/aimem-memory.instructions.md`,
  `.kiro/steering/aimem-memory.md`, generated memory agents, hooks, or this skill.
- Do not store secrets, credentials, tokens, personal data, temporary progress, unvalidated
  assumptions, one-off details, or full conversation transcripts.
- Require approval for user memory, personal preferences, low-confidence claims,
  deprecations, and deletions.
- Do not duplicate facts already represented clearly by authoritative code, tests, ADRs, or
  documentation.