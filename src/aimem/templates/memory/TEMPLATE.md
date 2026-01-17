# Memory Template

Use this template whenever an agent initializes or adds memory. The canonical memory files
stay readable as Markdown, but every durable entry should be written with
`record_memory.py` so the embedded `aimem:record` metadata is valid and queryable.

## Entry Fields

- `scope`: `project`, `user`, `session`, or `agent`.
- `topic`: existing or new `##` heading in the target memory file.
- `kind`: `fact`, `command`, `convention`, `decision`, `gotcha`, `glossary`, or `note`.
- `status`: `active` for usable memory; `deprecated`, `superseded`, or `invalid` for lifecycle changes.
- `source`: repository evidence, user approval, or migration source such as `README.md`, `pyproject.toml`, `user`, or `migration`.
- `confidence`: decimal from `0` to `1`; use higher values only for verified repository evidence or explicit user statements.
- `validity`: optional validity window using `--valid-from` and `--valid-until` ISO timestamps.
- `relationships`: optional `TYPE:ID` links such as `supersedes:mem_abc123`, `relates_to:mem_def456`, or `contradicts:mem_xyz789`.
- `text`: concise, self-contained Markdown sentence that remains useful without conversation history.

## Project Memory Sections

Fill `{{PROJECT_MEMORY}}` with durable team-shared facts under these headings:

- `Conventions`: coding, review, naming, formatting, or workflow rules.
- `Architecture`: stable modules, ownership boundaries, data flows, generated artifacts, or integration points.
- `Commands`: verified build, test, lint, run, package, or release commands.
- `Gotchas`: recurring pitfalls, platform constraints, broken paths, or non-obvious setup details.
- `Glossary`: domain terms, acronyms, product names, or repository-specific vocabulary.

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
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope project --topic "Commands" --kind command --source "pyproject.toml" --confidence 0.9 --text "Run the full test suite with `python -m pytest -q`."
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope project --topic "Architecture" --kind decision --source "README.md" --confidence 0.8 --relationship relates_to:mem_example --text "Memory hooks are generated into `.aimem/hooks/` and run without importing the installed aimem package."
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope session --topic "Current goal" --kind note --source "user" --confidence 1 --text "Initialize aimem memory for this repository."
```

Convert legacy bullets without changing their visible text:

```sh
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope project
```

## Fill Rules

- Inspect repository evidence before writing project memory.
- Prefer updating or deprecating existing entries over adding duplicates.
- Keep each entry short enough to scan quickly.
- Do not record secrets, credentials, personal data, transient plans, unvalidated assumptions, full conversation transcripts, or facts already obvious from nearby source code.
- If evidence is weak, record a session note or ask for approval instead of creating durable project or user memory.