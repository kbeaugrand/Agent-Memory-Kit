---
name: generate-project-instructions
description: Analyze repository practices and generate evidence-based, scoped guidance for the configured AI coding platforms.
user-invocable: true
---

# Generate Project Instructions

Analyze the current repository and create or update native project guidance for its configured AI
coding platforms. Treat code, tests, configuration, and authoritative documentation as evidence.

## Procedure

1. Determine the enabled platforms from the native aimem skill or configuration already present:
   `.github/skills/generate-project-instructions/SKILL.md` or GitHub Copilot instruction files
   enable GitHub Copilot; `.kiro/skills/generate-project-instructions/SKILL.md` or Kiro steering
   files enable Kiro. Generate guidance only for enabled platforms. Never create configuration
   for a platform that is not already enabled in the repository.
2. Inspect the existing instruction or steering files for enabled platforms. Preserve
   user-authored guidance and aimem-managed markers.
3. Identify languages, frameworks, module boundaries, validation commands, dependency rules,
   naming conventions, and repeated implementation patterns. Confirm each rule with authoritative
   configuration, documentation, representative files, or tests.
4. Exclude generated output, vendored dependencies, caches, build artifacts, and isolated legacy
   code unless authoritative project guidance establishes them as current practice.
5. Apply the lesson-learning scope rules before creating or updating a file. Determine each rule's
   exact applicability by file type, directory, component, workflow, or the whole repository.
   Do not group rules with different targets merely because they concern the same technology.
6. Keep each focused file concise and cohesive. Split rules into separate files when they do not
   share the same applicability so agents load only guidance relevant to the current target.
   Prefer actionable, non-obvious instructions over broad repository summaries.
7. Create or minimally update files for each enabled platform:
   - GitHub Copilot: place targeted rules in
     `.github/instructions/<concern>.instructions.md` with the narrowest accurate workspace-relative
     `applyTo` glob. Use multiple globs only when every rule applies to every listed target. Reserve
     `applyTo: "**"` and `.github/copilot-instructions.md` for genuinely repository-wide rules.
   - Kiro: place targeted rules in `.kiro/steering/<concern>.md` with
     `inclusion: fileMatch` and the narrowest accurate `fileMatchPattern`. Use `inclusion: always`
     only for genuinely global rules, placed in the appropriate `product.md`, `tech.md`, or
     `structure.md` file.
8. Prefer updating an existing rule over adding a duplicate. Make minimal edits and preserve
   unrelated guidance when an existing file already owns the same concern and applicability.
9. Validate frontmatter, paths, scope, file cohesion, and consistency between enabled platforms.
   Report
   the evidence used and any uncertain practice intentionally omitted.

## Boundaries

- Do not create a separate memory directory, metadata index, proposal, or session transcript.
- Never edit aimem-managed marker content or this skill while generating guidance.
- Do not replace an existing instruction file wholesale when a focused update preserves unrelated
  guidance.
- Do not create instructions from guesses, temporary details, secrets, or personal preferences.