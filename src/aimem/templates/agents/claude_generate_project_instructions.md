---
name: generate-project-instructions
description: Analyze repository practices and generate an evidence-based project-knowledge skill.
tools: Read, Glob, Grep, Write, Edit, Bash
model: inherit
---

# Generate Project Instructions

Analyze the current repository and create or update the dedicated Claude Code project skill at
`.claude/skills/project-knowledge/`. Treat code, tests, configuration, and authoritative
documentation as evidence.

## Procedure

1. Inspect the existing `SKILL.md`, `reference.md`, and `examples.md` in the project-knowledge
   skill. Preserve validated user-authored knowledge.
2. Identify languages, frameworks, module boundaries, validation commands, dependency rules,
   naming conventions, and repeated implementation patterns. Confirm each rule with authoritative
   configuration, documentation, representative files, or tests.
3. Exclude generated output, vendored dependencies, caches, build artifacts, and isolated legacy
   code unless authoritative project guidance establishes them as current practice.
4. Keep `SKILL.md` concise: give it a specific discovery description, tell Claude when to apply
   the knowledge, and link to `reference.md` and `examples.md` for details.
5. Organize validated architecture, conventions, commands, workflows, and applicability details
   by concern in `reference.md`. State exact file types or directories when a lesson is scoped.
6. Put focused, minimal examples in `examples.md` only when they clarify how a referenced lesson
   should be applied. Link every example to its owning lesson and avoid copying large source files.
7. Prefer updating existing knowledge over adding a duplicate. Validate frontmatter, links,
   evidence, and consistency, then report the evidence used and uncertain practices omitted.

## Boundaries

- Do not create a separate memory directory, metadata index, proposal, or session transcript.
- Never edit this agent or the lesson-learning skill while generating project knowledge.
- Do not replace a support file wholesale when a focused update preserves unrelated knowledge.
- Do not create instructions from guesses, temporary details, secrets, or personal preferences.