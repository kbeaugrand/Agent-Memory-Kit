# Agent-scoped memory

Files in this directory hold **per-agent** memory: durable facts that matter to one
specific agent rather than the whole project. This mirrors coday's agent-scoped memory
(`memory list --project --agent=Dev`).

- One file per agent: `<agent-name>.md` (for example `Dev.md`, `Reviewer.md`).
- Same structure as project memory: `## Section` headings with readable `- ` bullet
	entries plus embedded `aimem:record` metadata.
- Committed with the project so the whole team shares each agent's memory.
- This `README.md` is documentation only and is never injected into context.

## Recording an agent-scoped fact

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/record_memory.py --scope agent --agent Dev --topic "Conventions" --text "..."
```

Use `--kind`, `--source`, `--confidence`, `--valid-from`, `--valid-until`, and
`--relationship TYPE:ID` to store provenance, confidence, validity windows, and
relationships.

## Listing / curating agent memory

```
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list --scope agent --agent Dev
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py list --scope agent --agent Dev --kind convention --format json
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py deprecate --scope agent --agent Dev --section Conventions --index 1
{{PYTHON_COMMAND}} {{HOOKS_DIR}}/manage_memory.py migrate --scope agent --agent Dev
```

## Injection

Agent memory is **not** injected automatically by default (`scopes.agent.inject` is
`"none"` in `.aimem/config.json`), because session hooks do not know which agent is
active. To inject a specific agent's memory, set the environment variable
`AIMEM_ACTIVE_AGENT=<name>` before the session starts, or set `scopes.agent.inject` to
`"all"` to inject every agent file. Agents can also read their own file on demand.
