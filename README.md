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
| Canonical memory | `.aimem/memory/project.md` (committed), `.aimem/memory/session/current.md` (ephemeral), `~/.aimem/memory/user.md` (global) |
| Project-local hook scripts | `.aimem/hooks/*.py` — self-contained, standard-library-only Python |
| Kiro | `.kiro/steering/aimem-memory.md`, `.kiro/agents/memory-initializer.md`, `.kiro/agents/memory-curator.md`, `.kiro/hooks/aimem-memory.kiro.hook` |
| GitHub Copilot | `.github/copilot-instructions.md` (block), `.github/instructions/aimem-memory.instructions.md`, `.github/agents/memory-initializer.agent.md`, `.github/agents/memory-curator.agent.md`, `.github/hooks/aimem-memory.json` |
| Cross-tool | `AGENTS.md` (block), `.gitignore` (block), `.aimem/config.json`, `.aimem/manifest.json` |

## How memory works after init

- **Read** — a `SessionStart` hook injects your memory into the agent's context
  automatically (Kiro via stdout, Copilot via `additionalContext`).
- **Write** — steering/instructions tell agents to persist durable facts with
  `record_memory.py`; a `memory-initializer` agent seeds project facts and a
  `memory-curator` agent consolidates and de-duplicates.
- **Guard** — a `PreToolUse` hook blocks writing secrets into memory files.
- **Consolidate** — a post-edit hook normalizes and de-duplicates memory files.

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

Runs the same Python CLI through a thin Node launcher. A Python 3.9+ interpreter must be on
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
aimem init --both --yes    # non-interactive: generate everything
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
