---
name: lesson-learning
description: Extract validated lessons, scope them by file glob or target, and record them in native project instructions or steering.
user-invocable: true
---

# Lesson Learning

Review the completed conversation in the current context. Do not read, copy, summarize, or
persist a transcript file.

## Procedure

1. Identify only durable, reusable lessons supported by an explicit user correction or decision,
   repeated confirmed behavior, a successful validation, or strong repository evidence.
2. Inspect existing GitHub Copilot instructions and Kiro steering for duplicates or conflicts.
   Prefer updating an existing rule over adding another one.
3. Determine the exact applicability of each lesson before writing it: file type, directory,
   component, workflow, or the whole repository. Do not group lessons with different targets in
   one instruction file merely because they were learned in the same session.
4. For GitHub Copilot, place targeted rules in a focused
   `.github/instructions/<concern>.instructions.md` file and set `applyTo` to the narrowest accurate
   workspace-relative glob, such as `**/*.py` or `src/api/**`. Use multiple globs only when every
   rule in the file applies to every listed target. Reserve `applyTo: "**"` and the global
   `.github/copilot-instructions.md` file for genuinely repository-wide rules.
5. For Kiro, use a focused `.kiro/steering/<concern>.md` file with `inclusion: fileMatch` and the
   narrowest accurate `fileMatchPattern`. Use `inclusion: always` only for genuinely global rules.
6. Keep each focused file concise and cohesive so agents load only knowledge relevant to the
   current file or target. Split a file when its rules no longer share the same applicability;
   this keeps instruction context bounded as knowledge grows.
7. Record genuinely repository-wide lessons outside aimem-managed markers and in the appropriate
   Kiro `product.md`, `tech.md`, or `structure.md` steering file.
8. Make minimal edits and preserve unrelated guidance. If no durable lesson emerged, do nothing.

## Boundaries

- Do not create a separate memory directory, metadata index, proposal, or session transcript.
- Never edit aimem-managed marker content or this skill while recording a lesson.
- Do not retain secrets, credentials, personal data, temporary progress, unvalidated assumptions,
  or one-off implementation details.
- Do not duplicate facts already represented clearly by authoritative code, tests, ADRs, or
  documentation.