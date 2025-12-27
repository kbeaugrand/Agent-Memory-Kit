---
inclusion: always
---

# AI Memory Protocol (managed by aimem)

This project uses a persistent, cross-tool memory system. Canonical memory lives in plain
Markdown files and is injected into your context automatically at the start of a session
and on each prompt. Memory is durable, validated, reusable knowledge. Treat injected
memory as established project context, but always follow the current explicit user request
first. If memory and the user's request conflict, follow the user and surface the conflict
instead of silently editing memory.

## Memory scopes

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared): durable repository
  conventions, architecture decisions, build/test/run commands, gotchas, and domain terms.
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project): stable individual
  preferences explicitly provided by the user.
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed): temporary working
  notes for the current task only.

Apply memory in this order:

1. Current explicit user request.
2. Path-specific project memory.
3. General project memory.
4. User memory.
5. Default memory policy.

When memories conflict, prefer the more specific entry and surface unresolved conflicts.
Never resolve semantic conflicts from timestamps alone.

## What becomes memory

A memory candidate must be important to future work, likely to remain true, reusable
across multiple future interactions, validated by the user or repository evidence, and
self-contained enough for a future agent to act on.

Never memorize secrets, credentials, tokens, private keys, sensitive personal data,
temporary plans, task progress, work in progress, unvalidated assumptions, one-off
implementation details, full conversation transcripts, or information already represented
clearly in code, tests, ADRs, or authoritative documentation.

## Recording memory

Never activate memory silently. When a durable candidate appears, determine the correct
scope, check for duplicates or contradictions, prefer updating an existing entry over
creating a duplicate, and present the exact proposed entry for approval.

Use this format:

```text
Memory candidate detected.

Scope: PROJECT | USER | SESSION
Action: ADD | UPDATE | DEPRECATE | DELETE
Target: <existing heading/entry or new memory>
Reason: <why this will help future interactions>

Proposed memory:
<exact content>

Approval required before activation.
```

Only after explicit approval, or when the user directly asks you to record memory, use the
recording script:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

Never edit generated assistant projection files directly. Change canonical memory files
through an approved memory action or the generated scripts.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` guard
blocks obvious secret writes, and a post-save hook normalizes and de-duplicates memory,
but approval and careful review are still required. Keep memory safe to commit and share.

## Curation

Keep memory concise. When it grows or drifts, switch to the **memory-curator** agent to
review candidates, consolidate duplicates, and propose stale entries for deprecation or
deletion before changing active memory.
