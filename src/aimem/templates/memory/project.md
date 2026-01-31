# Project Memory

<!--
Canonical PROJECT memory for AI software development agents. Commit this Markdown file
with the repository. It is the human-readable source of truth; complete machine metadata
lives in `.aimem/index/project.json`.

RECORD here automatically when repository evidence or a successful check validates a
reusable problem-solving lesson, or after explicit approval or direct user instruction.
Eligible content includes durable repository facts, root causes and fixes, diagnostic
workflows, validation commands, architecture rules, conventions, dependency rules, known
limitations, domain language, and project-specific mistakes that help a future agent write
correct code. Check for duplicates and contradictions before adding or updating an entry.
DO NOT record: secrets, tokens, passwords, personal data, temporary plans, task progress,
work in progress, unvalidated assumptions, one-off implementation details, full
conversation transcripts, or facts that do not improve future coding decisions.

Preferred way to add an entry:
  {{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope project --topic "Architecture" --priority high --evidence source_code --validation-status verified --source "README.md" --text "..."

Before initializing or filling project memory, read {{MEMORY_TEMPLATE}} and use its
curation rules. Every durable entry should answer at least one question: how should I
implement this, what must never be done, what rule exists, where is it implemented, which
pattern should I follow, or how do I validate my work?

Entry shape:
- 🔥 Critical Rule: Data access must always go through `IRepository<T>`.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: docs/architecture.md
  Verified from: Domain/Repositories/IRepository.cs
  Related: relates_to mem_repository_pattern
  Keywords: repository, persistence, database
  <!-- aimem:id=mem_example -->

Keep only the lightweight `aimem:id` comment in Markdown. Store full metadata in
`.aimem/index/project.json`; migrate older embedded `aimem:record` JSON comments with:
  {{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope project

Review or curate entries with:
  {{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list --scope project

Use priorities intentionally: Critical and High entries should guide retrieval before
recency. Prefer Verified Source Code, ADR, Documentation, or User Validated evidence over
Agent Inferred notes. Mark stale entries Deprecated instead of silently deleting them.
This header comment is stripped before injection, so it costs no context tokens.
-->

## Architecture

## Architectural Rules

## Coding Standards

## Dependency Rules

## Repository Structure

## Build and Validation

## Testing

## Deployment

## Security

## Performance

## Frameworks

## Patterns

## Domain

## Workflows

## How to Extend This Project

## Common Mistakes

## Architectural Decisions

## Known Limitations

## External Services

## Architecture Diagrams

## Glossary
