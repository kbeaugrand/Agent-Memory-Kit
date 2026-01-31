---
name: lesson-learning
description: Extract validated lessons and record them in the dedicated project-knowledge skill.
user-invocable: true
---

# Lesson Learning

Review the completed conversation in the current context. Do not read, copy, summarize, or
persist a transcript file.

## Procedure

1. Identify only durable, reusable lessons supported by an explicit user correction or decision,
   repeated confirmed behavior, a successful validation, or strong repository evidence.
2. Inspect `.claude/skills/project-knowledge/reference.md` and `examples.md` for duplicates or
   conflicts. Prefer updating an existing lesson over adding another one.
3. Record durable facts, conventions, commands, workflows, and applicability details in
   `reference.md`, organized into concise sections by concern.
4. Add or update an entry in `examples.md` only when a focused example makes a lesson materially
   easier to apply. Link it clearly to the owning lesson and avoid copying large source files.
5. Keep `SKILL.md` as a concise entrypoint that links to its support files. Change it only when the
   skill's discovery description or navigation needs to change.
6. Make minimal edits and preserve unrelated knowledge. If no durable lesson emerged, do nothing.

## Boundaries

- Do not create a separate memory directory, metadata index, proposal, or session transcript.
- Never edit this lesson-learning skill while recording a lesson.
- Do not retain secrets, credentials, personal data, temporary progress, unvalidated assumptions,
  or one-off implementation details.
- Do not duplicate facts already represented clearly by authoritative code, tests, ADRs, or
  documentation.