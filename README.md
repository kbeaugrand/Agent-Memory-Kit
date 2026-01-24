# aimem

**Initialize or update cross-tool AI agent memory for a project.**

`aimem` is a zero-dependency Python CLI with a single job: run `aimem init` once and it
scaffolds a complete, persistent **agent memory** system that works across
[Kiro](https://kiro.dev) and [GitHub Copilot](https://code.visualstudio.com/docs/copilot/overview).

After initialization, all memory behavior is implemented by the generated configuration —
you do **not** need the `aimem` executable at runtime. You only rerun `aimem init` to
repair or update the generated files.

## What it generates

| Layer | Files |
| --- | --- |
| Canonical memory | `.aimem/memory/project.md` (committed), `.aimem/memory/session/current.md` (ephemeral), `.aimem/memory/agents/<agent>.md` (per-agent, committed), `~/.aimem/memory/user.md` (global) |
| Memory metadata index | `.aimem/index/project.json` (committed support data for reviewable metadata and deterministic retrieval) |
| Project-local hook scripts | `.aimem/hooks/*.py` — self-contained, standard-library-only Python |
| Kiro | `.kiro/steering/aimem-memory.md`, `.kiro/steering/product.md`, `.kiro/steering/tech.md`, `.kiro/steering/structure.md`, `.kiro/agents/memory-initializer.md`, `.kiro/agents/memory-curator.md`, `.kiro/hooks/aimem-memory.kiro.hook` |
| GitHub Copilot | `.github/copilot-instructions.md` (block), `.github/instructions/aimem-memory.instructions.md`, `.github/agents/memory-initializer.agent.md`, `.github/agents/memory-curator.agent.md`, `.github/hooks/aimem-memory.json` |
| Cross-tool | `AGENTS.md` (block), `.gitignore` (block), `.aimem/config.json`, `.aimem/manifest.json` |

## How memory works after init

- **Read** — generated hooks inject your memory into the agent's context automatically
  (Kiro via stdout on `SessionStart` and `UserPromptSubmit`, Copilot via
  `additionalContext` on `SessionStart`). Injected memory is size-capped with a curation
  reminder when it grows large, and deprecated entries are excluded.
- **Propose** — steering/instructions tell agents to identify durable memory candidates,
  show the exact proposed entry, explain the scope and reason, and ask before activation.
- **Write** — after explicit approval, or when you directly ask the agent to record
  memory, agents persist entries with `record_memory.py` (add `--scope agent --agent <name>`
  for per-agent memory). Recorded entries keep plain Markdown text with a lightweight
  `aimem:id` comment, while complete metadata lives in `.aimem/index/`: kind, priority,
  evidence, validation status, source, verified-from paths, confidence, validity,
  keywords, and relationships. A `memory-initializer` agent can seed curated project
  rules, workflows, repository structure, dependency rules, validation commands, common
  mistakes, decisions, and diagrams during explicit initialization; a `memory-curator`
  agent reviews, consolidates, and de-duplicates approved memory.
- **Manage** — `manage_memory.py` lists, filters by priority/evidence/validation/source/
  keyword/relationship, exports JSON, deletes, deprecates (a reversible soft-delete),
  restores, or migrates individual entries, addressed by scope, section, and 1-based
  index. Migration converts legacy plain bullets or embedded `aimem:record` comments into
  lightweight Markdown plus sidecar metadata.
- **Guard** — a `PreToolUse` hook blocks writing secrets into memory files.
- **Consolidate** — a post-edit hook normalizes and de-duplicates memory files while
  preserving deprecated (soft-deleted) entries.

Memory is durable, validated, reusable knowledge optimized for future coding decisions.
Project memory is committed and shared with the team. User memory is personal and stays
in your home directory. Session memory is temporary scratch space for the current task and
is not durable memory. Agent memory holds durable facts specific to one agent, committed
under `.aimem/memory/agents/` and not injected by default (set `AIMEM_ACTIVE_AGENT` or
`scopes.agent.inject` to inject it).

Agents must not silently activate durable memory. A candidate should be important to
future work, likely to remain true, reusable across future interactions, validated by the
user or repository evidence, and self-contained enough for a future agent to act on.

Do not memorize secrets, credentials, tokens, private keys, sensitive personal data,
temporary plans, task progress, work in progress, unvalidated assumptions, one-off
implementation details, or full conversation transcripts. If explicit user instructions
conflict with existing memory, the current request wins and the conflict should be
surfaced instead of silently editing memory.

## Install & run

`aimem` is a Python CLI. It can be installed from the Git repository directly — no
publication to PyPI or npm is required.

### From Git with pipx (recommended for the CLI)

```bash
pipx install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init
```

### From Git with pip

```bash
pip install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init
```

### Run once with uvx (no install)

```bash
uvx --from git+https://github.com/kbeaugrand/Agent-Memory-Kit.git aimem init
```

### From Git with npx

Runs the same Python CLI through a thin Node launcher. A Python 3.10+ interpreter must be on
`PATH`; no pip install is required.

```bash
npx github:kbeaugrand/Agent-Memory-Kit init
```

> Once the package is published, `pipx install aimem`, `pip install aimem`, and
> `npx aimem init` will work as well.

## Usage

```text
aimem --help
aimem --version
aimem init --help

aimem init                 # interactive: choose Kiro, Copilot, or both
aimem init --both --yes    # non-interactive: accept defaults and generate everything
aimem init --both --no-input # non-interactive: use defaults, suitable for CI
aimem init --kiro          # only Kiro artifacts
aimem init --copilot       # only Copilot artifacts
aimem init --dry-run       # preview changes without writing
aimem init --user          # also set up global user memory in your home directory
```

Rerunning `aimem init` is safe and idempotent: aimem-owned files are reconciled, shared
files are updated only inside clearly marked managed blocks, and your seed memory files
are never overwritten. Any file you modified that aimem needs to rewrite is backed up
under `.aimem/backups/` first.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

## License

MIT — see [LICENSE](LICENSE).
