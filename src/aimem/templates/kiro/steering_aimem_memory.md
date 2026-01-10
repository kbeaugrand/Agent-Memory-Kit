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

## Context vs memory

Context is everything available right now: the current request, open files, recent
conversation, and injected memory. Memory is only the small, durable subset worth carrying
into *future* sessions. Keep them distinct:

- Do not treat transient conversation as memory, and never dump everything into memory.
- Prefer summarizing a long thread over memorizing it.
- Oversized or noisy memory degrades answers as much as missing memory; curate when it
  grows. Injected memory is capped with a reminder when it gets large.

## Memory scopes

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared): durable repository
  conventions, architecture decisions, build/test/run commands, gotchas, and domain terms.
- **User memory** — `{{USER_MEMORY}}` (personal, cross-project): stable individual
  preferences explicitly provided by the user.
- **Session memory** — `{{SESSION_MEMORY}}` (ephemeral, not committed): temporary working
  notes for the current task only.
- **Agent memory** — `{{AGENTS_MEMORY_DIR}}/<agent>.md` (committed, per-agent): durable
  facts specific to one agent rather than the whole team. Not injected by default; see
  "Managing memory".

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

New entries are versioned structured records embedded inside readable Markdown bullets.
The current schema stores `schema_version`, `id`, `scope`, `kind`, `status`, `source`,
`confidence`, `validity`, and `relationships`. Use `--kind`, `--source`, `--confidence`,
`--valid-from`, `--valid-until`, and `--relationship TYPE:ID` when provenance, validity,
or relationships matter.

Never edit generated assistant projection files directly. Change canonical memory files
through an approved memory action or the generated scripts.

## Managing memory

Memory entries are addressable by scope, section, and 1-based index. Inspect and curate
them with the management script instead of hand-editing:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list --scope project --kind command --source README.md --format json
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py deprecate --scope project --section Gotchas --index 2
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py restore --scope project --section Gotchas --index 2
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py delete --scope project --match "outdated note"
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope project
```

Prefer **deprecate** (a reversible soft-delete) over **delete**: a deprecated entry stays
on disk but is excluded from injected context, so history is preserved and mistakes are
recoverable. Hard-delete only after review. Use **migrate** to convert legacy plain
Markdown bullets into structured records without changing their visible text. Record
agent-specific facts with `record_memory.py --scope agent --agent <name>`.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` guard
blocks obvious secret writes, and a post-save hook normalizes and de-duplicates memory,
but approval and careful review are still required. Keep memory safe to commit and share.

## Curation

Keep memory concise. When a section grows past its warning threshold, drifts, or fills
with stale entries, switch to the **memory-curator** agent to review candidates,
consolidate duplicates, deprecate stale entries (a reversible soft-delete), and delete
only after review.
