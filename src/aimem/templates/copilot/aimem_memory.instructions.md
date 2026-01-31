---
applyTo: "**"
---

# AI Memory Protocol (managed by aimem)

This project uses a persistent, cross-tool memory system. Canonical memory lives in plain
Markdown files and is injected into your context automatically at the start of a session.
Memory is durable, validated, reusable knowledge. Treat injected memory as established
project context, but always follow the current explicit user request first. If memory and
the user's request conflict, follow the user and surface the conflict instead of silently
editing memory.

## Context vs memory

Context is everything available right now: the current request, open files, recent
conversation, and injected memory. Memory is only the small, durable subset worth carrying
into *future* sessions. Keep them distinct:

- Do not treat transient conversation as memory, and never dump everything into memory.
- Prefer summarizing a long thread over memorizing it.
- Oversized or noisy memory degrades answers as much as missing memory; curate when it
  grows. Injected memory is capped with a reminder when it gets large.

## Memory scopes

- **Project memory** — `{{PROJECT_MEMORY}}` (committed, team-shared): curated repository
  rules, dependency directions, workflows, validation commands, decisions, patterns,
  common mistakes, domain terms, and extension guidance that help future agents code
  correctly.
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
For project memory, prefer actionable rules, workflows, dependency constraints,
validation steps, extension checklists, decisions, and common mistakes over broad
documentation summaries.

Never memorize secrets, credentials, tokens, private keys, sensitive personal data,
temporary plans, task progress, work in progress, unvalidated assumptions, one-off
implementation details, full conversation transcripts, or information already represented
clearly in code, tests, ADRs, or authoritative documentation.

## Recognizing durable lessons

Recognizing and recording durable lessons is the agent's responsibility. Hooks manage the
memory lifecycle and use the `lesson-learning` skill to request one review turn after a
completed agent turn; hook scripts do not parse transcripts or author memory themselves.
As you work, watch for reusable lessons and review the completed session before your final
response. Automatically record a high-confidence lesson in project memory when it is
supported by an explicit user correction or decision, repeated confirmed behavior, a
successful check, or strong consistency with repository evidence and captures:

- The user corrects a repository rule, convention, or problem-solving approach.
- You confirm a non-obvious root cause or fix after debugging.
- You verify a build, test, or validation command or workflow that future agents will
  reuse.
- You identify and confirm a recurring mistake, gotcha, or constraint.
- A design or architectural decision, or a dependency direction, is made and validated.
- A domain term or naming convention is clarified.

Recognize only validated, reusable lessons. Never promote unvalidated assumptions, work
in progress, or task progress; keep them in session notes or nowhere until confirmed.
Do not duplicate facts already represented clearly in code, tests, ADRs, or authoritative
documentation.

When a high-confidence lesson is also a prescriptive coding rule, update the most
appropriate user-owned Copilot instruction or Kiro steering file, or create a focused one
when no existing owner fits. Never edit aimem-managed instructions, steering, hooks,
agents, or skills; `aimem init` replaces those files.

## Recording memory

For high-confidence repository problem-solving lessons, use project scope by default. Check for
duplicates and contradictions, prefer updating an existing entry over creating a
duplicate, then activate the concise, actionable add or update without interrupting the
user. Report automatically activated memories in your final response.

Explicit approval is still required before recording user memory, inferred preferences,
uncertain claims, or changes outside this automatic category. Also require approval before
deprecating or deleting active memory. Never automatically record secrets, personal data,
full conversation transcripts, temporary plans, or one-off implementation details.

Use this format:

```text
Memory candidate detected.

Scope: PROJECT | USER | SESSION
Action: ADD | UPDATE | DEPRECATE | DELETE
Target: <existing heading/entry or new memory>
Reason: <why this will help future interactions>

Proposed memory:
<exact content>

Activation: AUTOMATIC_PROJECT | APPROVAL_REQUIRED
```

Use the MCP memory service when it is available. For an automatically validated project
lesson, inspect existing memory, call `memory_propose`, and then call `memory_approve`
yourself. For approval-required changes, stop after the proposal until the user approves:

```
memory_propose -> memory_approve
memory_search | memory_get | memory_context | memory_handoff | memory_conflicts
```

`memory_context` returns budgeted, explainable context with included and omitted entries.
`memory_propose` is non-mutating; durable memory is activated only by `memory_approve`,
which the agent may call automatically only for the validated project lessons defined
above. Tool outputs are provider-neutral JSON envelopes so GitHub Copilot, Kiro, and
custom agents can use the same memory service.

If MCP is unavailable, use the recording script:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope <project|user|session> --topic "<Topic>" --text "<concise fact>"
```

New entries are readable Markdown blocks with lightweight `aimem:id` comments; complete
metadata lives in `.aimem/index/`. Use `--kind`, `--priority`, `--evidence`,
`--validation-status`, `--source`, `--verified-from`, `--keyword`, `--confidence`,
`--valid-from`, `--valid-until`, and `--relationship TYPE:ID` when provenance,
trustworthiness, retrieval hints, validity, or relationships matter.

When initializing memory, read the installed template at `{{MEMORY_TEMPLATE}}` and fill
memory according to its section guide and field definitions.

Never edit generated assistant projection files directly. Change canonical memory files
through the governed MCP flow or the generated scripts.

## Managing memory

Memory entries are addressable by scope, section, and 1-based index. Inspect and curate
them with MCP tools first (`memory_search`, `memory_get`, `memory_conflicts`,
`memory_handoff`) and with the management script as a fallback instead of hand-editing:

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list --scope project --priority critical --evidence source_code --format json
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py deprecate --scope project --section "Common Mistakes" --index 2
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py restore --scope project --section "Common Mistakes" --index 2
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py delete --scope project --match "outdated note"
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope project
```

Prefer **deprecate** (a reversible soft-delete) over **delete**: a deprecated entry stays
on disk but is excluded from injected context, so history is preserved and mistakes are
recoverable. Hard-delete only after review. Use **migrate** to convert legacy plain
Markdown bullets or embedded `aimem:record` comments into lightweight Markdown plus
sidecar metadata without changing visible text. Record agent-specific facts with
`record_memory.py --scope agent --agent <name>`.

## Security

Never store secrets, tokens, passwords, or personal data in memory. A `PreToolUse` hook
blocks obvious secret writes, and a `PostToolUse` hook normalizes and de-duplicates memory
files, but careful review is still required. Keep memory safe to commit and share.

## Curation

Keep memory concise. When a section grows past its warning threshold, drifts, or fills
with stale entries, switch to the **memory-curator** agent to review candidates,
consolidate duplicates, deprecate stale entries (a reversible soft-delete), and delete
only after review.
