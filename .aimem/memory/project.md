# Project Memory

<!--
Canonical PROJECT memory for AI software development agents. Commit this Markdown file
with the repository. It is the human-readable source of truth; complete machine metadata
lives in `.aimem/index/project.json`.

RECORD here only after explicit approval or direct user instruction: durable repository
facts, architecture rules, conventions, workflows, validation commands, dependency rules,
known limitations, domain language, and project-specific mistakes that help a future
agent write correct code.
DO NOT record: secrets, tokens, passwords, personal data, temporary plans, task progress,
work in progress, unvalidated assumptions, one-off implementation details, full
conversation transcripts, or facts that do not improve future coding decisions.

Preferred way to add an entry:
  python3 .aimem/hooks/record_memory.py --scope project --topic "Architecture" --priority high --evidence source_code --validation-status verified --source "README.md" --text "..."

Before initializing or filling project memory, read .aimem/memory/TEMPLATE.md and use its
curation rules. Every durable entry should answer at least one question: how should I
implement this, what must never be done, what rule exists, where is it implemented, which
pattern should I follow, or how do I validate my work?

Entry shape examples live in `.aimem/memory/TEMPLATE.md`.

Keep only the lightweight `aimem:id` comment in Markdown. Store full metadata in
`.aimem/index/project.json`; migrate older embedded `aimem:record` JSON comments with:
  python3 .aimem/hooks/manage_memory.py migrate --scope project

Review or curate entries with:
  python3 .aimem/hooks/manage_memory.py list --scope project

Use priorities intentionally: Critical and High entries should guide retrieval before
recency. Prefer Verified Source Code, ADR, Documentation, or User Validated evidence over
Agent Inferred notes. Mark stale entries Deprecated instead of silently deleting them.
This header comment is stripped before injection, so it costs no context tokens.
-->

## Architecture
- ⭐ High Structure: aimem is a Python 3.10+ CLI that initializes repository-local AI memory artifacts for GitHub Copilot and Kiro; after init, generated files provide the memory workflow, while the optional MCP server uses the installed package runtime.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: README.md; pyproject.toml; src/aimem/cli.py
  Verified from: README.md, pyproject.toml, src/aimem/cli.py
  Keywords: cli, copilot, kiro, mcp
  <!-- aimem:id=mem_182ae12dd911a996 -->

## Architectural Rules
- 🔥 Critical Rule: Generated project-local hook scripts under `.aimem/hooks/*.py` must remain self-contained and standard-library-only; tests assert the generated hooks compile and do not import the installed `aimem` package.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: README.md; tests/test_hook_scripts.py
  Verified from: README.md, tests/test_hook_scripts.py
  Keywords: generated-files, hooks, stdlib
  <!-- aimem:id=mem_14bb566a30c8f65a -->
- 🔥 Critical Rule: `aimem init` must stay idempotent: seed files are preserved unless forced, managed files are backed up before overwrite when locally modified, shared files update only the managed block, and JSON MCP configs are merged without dropping other servers.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: tests/test_idempotency.py; src/aimem/core/writer.py
  Verified from: tests/test_idempotency.py, src/aimem/core/writer.py
  Keywords: backups, idempotency, init, seed-files
  <!-- aimem:id=mem_e7cae677d8a68eda -->

## Coding Standards

## Dependency Rules
- ⭐ High Rule: The npm/npx package is only a thin Node launcher for the Python CLI: it requires Python 3.10+, sets `PYTHONPATH` to the bundled `src` directory, and forwards arguments to `python -m aimem`.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: bin/aimem.js; package.json
  Verified from: bin/aimem.js, package.json
  Keywords: launcher, npm, npx, python
  <!-- aimem:id=mem_84242c849995aa7a -->

## Repository Structure
- ⭐ High Structure: Repository layout: `src/aimem/cli.py` wires subcommands, `commands/` implements CLI commands, `core/` owns config, manifest, paths, rendering, writer, memory store, and vector database behavior, `mcp/` exposes provider-neutral memory tools, `templates/` contains generated artifacts, and `tests/` covers CLI, init, hooks, MCP, idempotency, and rendering.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: repository layout; src/aimem/cli.py; src/aimem/mcp/server.py
  Verified from: src/aimem/cli.py, src/aimem/commands/init.py, src/aimem/core/memory_store.py, src/aimem/mcp/server.py
  Keywords: cli, core, repository, templates
  <!-- aimem:id=mem_11690c0d9797362e -->

## Build and Validation
- ⭐ High Command: For local development validation, use `ruff check .`, `ruff format --check .`, `mypy`, and `pytest`; these commands are documented in the README and configured in pyproject.toml.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: README.md; pyproject.toml
  Verified from: README.md, pyproject.toml
  Keywords: mypy, pytest, ruff, validation
  <!-- aimem:id=mem_db956484b28ba3eb -->
- ⭐ High Workflow: Run repository regeneration with `.\.venv\Scripts\python.exe -m aimem init --both --no-input`; using a different Python interpreter rewrites the generated MCP command paths and creates unrelated configuration churn.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: validated init workflow
  Verified from: .vscode/mcp.json
  Keywords: aimem, mcp, venv
  <!-- aimem:id=mem_41ca63af5ae886ef -->
## Testing

## Deployment

## Security
- 🔥 Critical Rule: Never store secrets, tokens, passwords, private keys, sensitive personal data, or full conversation transcripts in memory; generated guards block secret-like writes into memory files and the recorder redacts configured secret patterns.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: README.md; .aimem/config.json; tests/test_hook_scripts.py
  Verified from: README.md, .aimem/config.json, tests/test_hook_scripts.py
  Keywords: guard, memory, redaction, secrets
  <!-- aimem:id=mem_980186901c10d2e9 -->

## Performance

## Frameworks

## Patterns
- 🔥 Critical Pattern: Canonical memory stays as readable Markdown, while rich metadata belongs in `.aimem/index/*.json`; Markdown entries should keep only lightweight `<!-- aimem:id=... -->` comments, and agents should use `record_memory.py` or `manage_memory.py` to keep Markdown and sidecar indexes synchronized.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: .aimem/memory/TEMPLATE.md; README.md; tests/test_hook_scripts.py
  Verified from: .aimem/memory/TEMPLATE.md, README.md, tests/test_hook_scripts.py
  Keywords: index, manage_memory, markdown, record_memory
  <!-- aimem:id=mem_30f26f11a81aa10d -->

## Domain

## Workflows
- 🔥 Critical Workflow: Durable MCP memory writes require `memory_propose` followed by `memory_approve`; proposals are local review state, approval writes Markdown plus the sidecar index, and rejection leaves memory unchanged.
  Evidence: ✓ Documentation, ✓ Source Code
  Validation: Verified
  Source: README.md; src/aimem/mcp/server.py; tests/test_mcp_service.py
  Verified from: README.md, src/aimem/mcp/server.py, tests/test_mcp_service.py
  Keywords: mcp, memory_approve, memory_propose, proposals
  <!-- aimem:id=mem_741ba6eb44a0cf14 -->

## How to Extend This Project
- ⭐ High Workflow: When changing generated init artifacts, update the templates under `src/aimem/templates/` and the tests that assert generated tree shape, hook JSON, instruction frontmatter, unresolved template tokens, scope boundaries, and config budgets.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: tests/test_generated_artifacts.py; src/aimem/commands/init.py
  Verified from: tests/test_generated_artifacts.py, src/aimem/commands/init.py
  Keywords: generated-artifacts, init, templates, tests
  <!-- aimem:id=mem_b33e0ba394356ef3 -->

## Common Mistakes

## Architectural Decisions

## Known Limitations

## External Services

## Architecture Diagrams

## Glossary

## Commands
- High Workflow: Validate packaged templates from an installed distribution, not only the source checkout: the CI `install-from-git` job loads `skills/lesson_learning.md` through `aimem.templates.loader`, runs `aimem init --both`, and asserts both generated `SKILL.md` files exist.
  Evidence: Source Code
  Validation: Verified
  Source: .github/workflows/ci.yml; local wheel and init smoke checks
  Verified from: .github/workflows/ci.yml, pyproject.toml, package.json
  Keywords: ci, packaging, skill, smoke-test, templates
  <!-- aimem:id=mem_1cfea5f3238b742d -->
