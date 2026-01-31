---
name: generate-project-instructions
description: Analyze repository practices and generate evidence-based, scoped project instructions for GitHub Copilot and Kiro.
user-invocable: false
---

# Generate Project Instructions

Analyze the current repository and create or update corresponding project instructions for
GitHub Copilot and Kiro. Treat existing code, tests, configuration, and authoritative project
documentation as evidence; do not infer conventions from a single incidental example.

## Procedure

1. Inspect existing `AGENTS.md`, `.github/copilot-instructions.md`,
   `.github/instructions/**/*.instructions.md`, and `.kiro/steering/**/*.md` files. Preserve
   user-owned guidance and identify aimem-managed files that must not be edited.
2. Identify the repository's languages, frameworks, module boundaries, test organization,
   formatting and validation commands, dependency rules, naming conventions, and repeated
   implementation patterns. Confirm each proposed rule with configuration, documentation,
   multiple representative files, or tests.
3. Exclude generated output, vendored dependencies, caches, build artifacts, and isolated
   legacy code unless authoritative project guidance says they establish current practice.
4. Group only coherent rules that share the same applicability. Prefer concise, actionable,
   non-obvious instructions with a short rationale or a representative example where useful.
   Do not restate rules already enforced completely by formatters or linters.
5. Create or minimally update a corresponding pair for each concern:
   - GitHub Copilot: `.github/instructions/<concern>.instructions.md`
   - Kiro: `.kiro/steering/<concern>.md`
6. Use the narrowest accurate path-and-extension patterns. Multiple disjoint patterns are
   allowed when they express one coherent scope. Do not broaden a pattern to combine unrelated
   rules.
7. Validate frontmatter, paths, glob coverage, links, and consistency between each pair. Report
   the evidence used, files created or updated, and any uncertain practice intentionally omitted.

## Platform Formats

GitHub Copilot instruction files use frontmatter at the first line:

```yaml
---
name: "Descriptive Name"
description: "Use when working on <specific task or area>. Covers <keywords>."
applyTo: "src/**/*.py"
---
```

- Use `.github/instructions/*.instructions.md` for focused project rules.
- Use a string or YAML array for `applyTo`. Paths are workspace-relative glob patterns.
- Reserve `applyTo: "**"` for rules that apply to every file in the repository.
- Keep the description keyword-rich so Copilot can discover the instruction by task relevance.

Kiro steering files use one of these inclusion modes in frontmatter at the first line:

```yaml
---
inclusion: fileMatch
fileMatchPattern: "src/**/*.py"
---
```

- Use `fileMatch` for path- or extension-specific rules; the pattern can be a string or array.
- Use `inclusion: always` only for universal project rules.
- Use `inclusion: auto` with required `name` and `description` for task-relevant guidance that cannot be
  represented accurately by file paths.
- Use `inclusion: manual` only for specialized guidance that should be explicitly requested.
- Use `#[[file:relative/path]]` when a live workspace-file reference is more durable than copied
  content.

## Boundaries

- Never edit aimem-managed files, including `.github/instructions/aimem-memory.instructions.md`,
  `.kiro/steering/aimem-memory.md`, generated prompts, skills, agents, or hooks.
- Never replace an existing instruction file wholesale when a focused update will preserve
  unrelated user guidance.
- Do not create instructions for guesses, temporary implementation details, secrets, personal
  preferences, or conventions already contradicted by authoritative repository sources.
- Do not claim Copilot and Kiro support identical metadata. Keep rule content equivalent while
  using each platform's native inclusion format.