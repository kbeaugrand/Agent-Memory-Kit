---
name: generate-project-instructions
description: Analyze repository practices and generate evidence-based, scoped GitHub Copilot instructions and Kiro steering.
user-invocable: true
---

# Generate Project Instructions

Analyze the current repository and create or update native project guidance for GitHub Copilot
and Kiro. Treat code, tests, configuration, and authoritative documentation as evidence.

## Procedure

1. Inspect existing `.github/copilot-instructions.md`,
   `.github/instructions/**/*.instructions.md`, and `.kiro/steering/**/*.md` files. Preserve
   user-authored guidance and aimem-managed markers.
2. Identify languages, frameworks, module boundaries, validation commands, dependency rules,
   naming conventions, and repeated implementation patterns. Confirm each rule with authoritative
   configuration, documentation, representative files, or tests.
3. Exclude generated output, vendored dependencies, caches, build artifacts, and isolated legacy
   code unless authoritative project guidance establishes them as current practice.
4. Group only coherent rules with the same applicability. Prefer concise, actionable,
   non-obvious instructions over broad repository summaries.
5. Create or minimally update the corresponding native files:
   - GitHub Copilot: `.github/instructions/<concern>.instructions.md`
   - Kiro: `.kiro/steering/<concern>.md`
6. Use the narrowest accurate `applyTo` or Kiro inclusion metadata. Reserve repository-wide
   inclusion for rules that genuinely apply everywhere.
7. Validate frontmatter, paths, scope, and consistency between platforms. Report the evidence used
   and any uncertain practice intentionally omitted.

## Boundaries

- Do not create a separate memory directory, metadata index, proposal, or session transcript.
- Never edit aimem-managed marker content or this skill while generating guidance.
- Do not replace an existing instruction file wholesale when a focused update preserves unrelated
  guidance.
- Do not create instructions from guesses, temporary details, secrets, or personal preferences.