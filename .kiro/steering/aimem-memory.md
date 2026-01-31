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

- **Project memory** — `.aimem/memory/project.md` (committed, team-shared): curated repository
  rules, dependency directions, workflows, validation commands, decisions, patterns,
  common mistakes, domain terms, and extension guidance that help future agents code
  correctly.
- **User memory** — `~/.aimem/memory/user.md` (personal, cross-project): stable individual
  preferences explicitly provided by the user.
- **Session memory** — `.aimem/memory/session/current.md` (ephemeral, not committed): temporary working
  notes for the current task only.
- **Agent memory** — `.aimem/memory/agents/<agent>.md` (committed, per-agent): durable
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
For project memory, prefer actionable rules, workflows, dependency constraints,
validation steps, extension checklists, decisions, and common mistakes over broad
documentation summaries.

Never memorize secrets, credentials, tokens, private keys, sensitive personal data,
temporary plans, task progress, work in progress, unvalidated assumptions, one-off
implementation details, full conversation transcripts, or information already represented
clearly in code, tests, ADRs, or authoritative documentation.

## Recognizing durable lessons

Recognizing a durable lesson and initiating a proposal is your responsibility, not the
hooks'. Hooks only manage the memory lifecycle — they inject memory at session start and on
each prompt, guard against secret writes, and consolidate files after changes — and never
author memory on their own. As you work, watch for the moment a reusable lesson emerges and
pause to consider a proposal when, and only when, it is validated:

- The user states a durable preference, rule, or convention, or corrects your approach.
- You confirm a non-obvious root cause or fix after debugging.
- You verify a build, test, or validation command or workflow that future agents will
  reuse.
- You identify and confirm a recurring mistake, gotcha, or constraint.
- A design or architectural decision, or a dependency direction, is made and validated.
- A domain term or naming convention is clarified.

Recognize only validated, reusable lessons. Never propose from unvalidated assumptions,
work in progress, or task progress; implementation progress must not silently become
durable memory, so keep it in session notes or nowhere until it is confirmed.

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
MCP memory service when it is available:

```
memory_propose -> memory_approve
memory_search | memory_get | memory_context | memory_handoff | memory_conflicts
```

`memory_context` returns budgeted, explainable context with included and omitted entries.
`memory_propose` is non-mutating; durable memory is activated only by `memory_approve`
after explicit approval. Tool outputs are provider-neutral JSON envelopes so Kiro, GitHub
Copilot, and custom agents can use the same memory service.

If MCP is unavailable, use the recording script:

```
python3 .aimem/hooks/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

New entries are readable Markdown blocks with lightweight `aimem:id` comments; complete
metadata lives in `.aimem/index/`. Use `--kind`, `--priority`, `--evidence`,
`--validation-status`, `--source`, `--verified-from`, `--keyword`, `--confidence`,
`--valid-from`, `--valid-until`, and `--relationship TYPE:ID` when provenance,
trustworthiness, retrieval hints, validity, or relationships matter.

When initializing memory, read the installed template at `.aimem/memory/TEMPLATE.md` and fill
memory according to its section guide and field definitions.

Never edit generated assistant projection files directly. Change canonical memory files
through an approved memory action or the generated scripts.

## Managing memory

Memory entries are addressable by scope, section, and 1-based index. Inspect and curate
them with MCP tools first (`memory_search`, `memory_get`, `memory_conflicts`,
`memory_handoff`) and with the management script as a fallback instead of hand-editing:

```
python3 .aimem/hooks/manage_memory.py list
python3 .aimem/hooks/manage_memory.py list --scope project --priority critical --evidence source_code --format json
python3 .aimem/hooks/manage_memory.py deprecate --scope project --section "Common Mistakes" --index 2
python3 .aimem/hooks/manage_memory.py restore --scope project --section "Common Mistakes" --index 2
python3 .aimem/hooks/manage_memory.py delete --scope project --match "outdated note"
python3 .aimem/hooks/manage_memory.py migrate --scope project
```

Prefer **deprecate** (a reversible soft-delete) over **delete**: a deprecated entry stays
on disk but is excluded from injected context, so history is preserved and mistakes are
recoverable. Hard-delete only after review. Use **migrate** to convert legacy plain
Markdown bullets or embedded `aimem:record` comments into lightweight Markdown plus
sidecar metadata without changing visible text. Record agent-specific facts with
`record_memory.py --scope agent --agent <name>`.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` guard
blocks obvious secret writes, and a post-save hook normalizes and de-duplicates memory,
but approval and careful review are still required. Keep memory safe to commit and share.

## Curation

Keep memory concise. When a section grows past its warning threshold, drifts, or fills
with stale entries, switch to the **memory-curator** agent to review candidates,
consolidate duplicates, deprecate stale entries (a reversible soft-delete), and delete
only after review.
