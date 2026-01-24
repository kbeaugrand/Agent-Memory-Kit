# Memory Template

Use this template whenever an agent initializes, records, migrates, or curates memory.
Canonical memory files stay readable as Markdown. Full machine metadata belongs in the
sidecar index under `.aimem/index/`, and Markdown entries should keep only lightweight
`<!-- aimem:id=... -->` comments.

## Entry Fields

- `scope`: `project`, `user`, `session`, or `agent`.
- `topic`: existing or new `##` heading in the target memory file.
- `kind`: `fact`, `convention`, `recommendation`, `rule`, `workflow`, `command`, `decision`, `mistake`, `glossary`, `structure`, `diagram`, `limitation`, `pattern`, `external_service`, `gotcha`, or `note`.
- `priority`: `critical`, `high`, `medium`, or `low`. Retrieval should prefer priority before recency.
- `evidence`: one or more of `source_code`, `adr`, `documentation`, `user_validated`, or `agent_inferred`.
- `validation_status`: `verified`, `needs_review`, or `deprecated`.
- `source`: human-readable source that explains why the memory exists, such as `README.md`, `docs/adr/0001.md`, `user`, or `migration`.
- `verified_from`: optional source-code paths, tests, ADRs, or docs that verify the memory.
- `confidence`: internal decimal from `0` to `1`; keep review-facing trust in `evidence` and `validation_status`.
- `validity`: optional validity window using `--valid-from` and `--valid-until` ISO timestamps.
- `relationships`: optional `TYPE:ID` links such as `supersedes:mem_abc123`, `relates_to:mem_def456`, or `contradicts:mem_xyz789`.
- `keywords`: deterministic retrieval hints such as `repository`, `unitofwork`, `database`, or `pytest`.
- `text`: concise, self-contained Markdown that remains useful without conversation history.

## Entry Shape

```markdown
- 🔥 Critical Rule: Domain services never depend on Infrastructure components.
  Evidence: ✓ Source Code
  Validation: Verified
  Source: docs/architecture.md
  Verified from: src/domain/services.py
  Related: relates_to mem_clean_architecture
  Keywords: domain, infrastructure, dependency-rule
  <!-- aimem:id=mem_01JXXXX -->
```

## Project Memory Sections

Fill `{{PROJECT_MEMORY}}` with durable team-shared memory under retrieval-oriented headings:

- `Architecture`: stable module boundaries, runtime shape, high-level data flow.
- `Architectural Rules`: enforceable rules such as forbidden dependencies or persistence rules.
- `Coding Standards`: naming, formatting, review, style, and implementation conventions.
- `Dependency Rules`: allowed and forbidden dependency directions.
- `Repository Structure`: concise map of folders and ownership.
- `Build and Validation`: run, build, lint, format, coverage, packaging, and when to use each command.
- `Testing`: test frameworks, test layout, required test patterns, and fixture conventions.
- `Deployment`: release, hosting, packaging, and environment workflows.
- `Security`: secret handling, authentication, authorization, and unsafe patterns to avoid.
- `Performance`: important constraints, hot paths, caching rules, and scalability assumptions.
- `Frameworks`: project-specific framework usage and integration rules.
- `Patterns`: recurring implementation patterns agents should copy.
- `Domain`: durable business/domain concepts needed for correct code.
- `Workflows`: reusable procedures such as creating an entity, adding an endpoint, or shipping a release.
- `How to Extend This Project`: feature-addition checklist optimized for coding agents.
- `Common Mistakes`: actionable wrong/right pairs that prevent repeated errors.
- `Architectural Decisions`: decisions with reason, impact, and alternatives.
- `Known Limitations`: current constraints agents must respect.
- `External Services`: service contracts, queues, APIs, databases, and integration boundaries.
- `Architecture Diagrams`: Mermaid diagrams generated only from clear evidence.
- `Glossary`: project-specific terms and acronyms.

## Session Memory Sections

Fill `{{SESSION_MEMORY}}` only for current setup work:

- `Current goal`: the task being performed now.
- `Working notes`: short findings that may help finish this task.
- `Open questions`: unresolved questions that should not become durable facts yet.

## User Memory Sections

Fill `{{USER_MEMORY}}` only from explicit user-provided preferences:

- `Preferences`: stable communication, review, or coding preferences.
- `Tooling`: preferred shells, editors, package managers, or command variants.
- `Workflow`: stable process preferences that should apply across repositories.

## Recording Commands

Prefer commands like these instead of hand-editing bullets:

```sh
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope project --topic "Build and Validation" --kind command --priority high --evidence source_code --validation-status verified --source "pyproject.toml" --verified-from "tests/conftest.py" --keyword pytest --confidence 0.9 --text "Run the full test suite with `python -m pytest`."
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope project --topic "Architectural Rules" --kind rule --priority critical --evidence source_code --validation-status verified --source "src/domain" --keyword dependency-rule --text "Domain code must not import Infrastructure modules."
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope session --topic "Current goal" --kind note --priority medium --evidence user_validated --validation-status verified --source "user" --text "Initialize aimem memory for this repository."
```

Convert legacy bullets or embedded `aimem:record` comments without changing visible text:

```sh
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope project
```

## Fill Rules

- Inspect source code, tests, manifests, README files, ADRs, and existing instructions before writing project memory.
- Prefer rules, workflows, dependency directions, validation commands, extension checklists, common mistakes, and project-specific patterns over broad descriptions.
- Keep immutable facts, conventions, recommendations, decisions, and workflows as distinct memory types.
- Generate Mermaid diagrams only when the repository contains enough evidence to avoid invention.
- Prefer updating or deprecating existing entries over adding duplicates.
- Keep each entry short enough to scan quickly.
- Do not record secrets, credentials, personal data, transient plans, unvalidated assumptions, full conversation transcripts, or facts already obvious from nearby source code.
- If evidence is weak, record a session note or ask for approval instead of creating durable project or user memory.
