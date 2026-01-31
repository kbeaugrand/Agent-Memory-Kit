# aimem

**Persistent memory for AI coding agents, installed into your repository.**

`aimem` turns project knowledge into reviewable, durable agent memory for
[GitHub Copilot](https://code.visualstudio.com/docs/copilot/overview) and
[Kiro](https://kiro.dev). Run `aimem init` in a project and it generates the
instructions, hooks, memory files, and helper agents needed for coding agents to reuse
the same context across sessions and tools.

The generated hooks do not need an `aimem` package dependency after initialization. The
optional MCP memory service does: install the Python package when you want agents to use
the generated MCP tools.

## Value proposition

AI coding agents are most useful when they remember the things your team already learned:
architecture decisions, validation commands, repository conventions, common mistakes, and
tool-specific workflow rules. Without a memory layer, that knowledge often lives in a
chat transcript or disappears between sessions.

`aimem` gives you a governed memory system that is:

- **Portable**: one memory model works across GitHub Copilot and Kiro.
- **Reviewable**: project memory is plain Markdown committed with the repository.
- **Scoped**: project, session, user, and per-agent memory stay separate.
- **Governed**: validated project lessons can be activated automatically through an
  auditable proposal flow; sensitive or uncertain changes still require approval.
- **Safer by default**: generated guards block secrets from being written into memory.
- **Low maintenance**: generated hook scripts are self-contained, standard-library-only
  Python.

## Quick start

Install aimem globally, then initialize the project:

```bash
cd path/to/your-project
python -m pip install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
npx github:kbeaugrand/Agent-Memory-Kit init --both
```

Python 3.10+ and the globally installed `aimem` command must be available on `PATH`. The
generated IDE configuration starts the MCP server with `aimem mcp-server`. If you do not
want MCP integration, initialize with `--no-mcp` and skip the `pip` installation.

For a non-interactive setup, such as CI or scripted repository bootstrapping:

```bash
npx github:kbeaugrand/Agent-Memory-Kit init --both --no-input -C path/to/your-project
```

After init, ask your coding agent to seed or update memory in normal language:

```text
Initialize project memory for this repository.
Record this as project memory: run pytest before changing hook behavior.
Review and curate existing memory entries.
```

## How it fits your workflow

1. **Initialize once**: `aimem init` creates the memory files, tool instructions, hooks,
   and helper agents for the selected toolchains.
2. **Commit shared memory**: project memory and generated configuration live in the repo,
   while session memory stays ephemeral and user memory stays in your home directory.
3. **Let agents read context automatically**: generated hooks inject relevant memory at
   session start and prompt time, with size caps and curation reminders.
4. **Learn from completed work**: agents automatically preserve validated, reusable
  repository problem-solving lessons after checking for duplicates and conflicts.
5. **Curate over time**: memory can be consolidated, de-duplicated, deprecated, restored,
   filtered, migrated, or exported by the generated management scripts.
6. **Rerun safely**: `aimem init` is idempotent and can repair or update managed files
   without overwriting your seed memory.

## Install options

`aimem` is a Python 3.10+ CLI. It can be installed directly from this Git repository; no
PyPI or npm publication is required.

### pipx, recommended

```bash
pipx install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init
```

### pip

```bash
pip install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init
```

### uvx, no install

```bash
uvx --from git+https://github.com/kbeaugrand/Agent-Memory-Kit.git aimem init
```

### npx from Git

The npm package is a thin Node launcher for the same Python CLI. It is convenient for
one-shot initialization and requires Python 3.10+ on `PATH`.

```bash
npx github:kbeaugrand/Agent-Memory-Kit init
```

By default, init also writes IDE configuration for the MCP memory service. Install the
Python package into the interpreter selected by `npx` so that server remains available:

```bash
python -m pip install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
```

Use `--no-mcp` when you only want the generated files and hooks and do not want to install
the MCP server runtime.

Once packages are published, `pipx install aimem`, `pip install aimem`, and
`npx aimem init` will work as well.

## Usage

```text
aimem --help
aimem --version
aimem init --help

aimem init                         # interactive setup
aimem init --both                  # generate Kiro and Copilot artifacts
aimem init --kiro                  # generate only Kiro artifacts
aimem init --copilot               # generate only Copilot artifacts
aimem init --both --no-input       # non-interactive defaults, useful for CI
aimem init --yes                   # accept defaults without prompting; implies both
aimem init --user                  # also create global user memory
aimem init --no-user               # skip global user memory
aimem init --dry-run               # preview changes without writing
aimem init --force                 # rewrite managed/seed files; backups are still made
aimem init --no-mcp                # skip generated IDE MCP server config
aimem init -C path/to/project      # initialize a specific directory
aimem init --python-command "py -3" # command embedded in generated hooks
aimem mcp-server -C path/to/project # run the local stdio MCP memory server
```

Rerunning `aimem init` is safe and idempotent. aimem-owned files are reconciled, shared
files are updated only inside marked managed blocks, and seed memory files are preserved.
If a managed file must be rewritten after local edits, `aimem` saves a backup under
`.aimem/backups/` first.

## Memory scopes

| Scope | Location | Purpose |
| --- | --- | --- |
| Project | `.aimem/memory/project.md` | Durable team knowledge committed with the repository. |
| Session | `.aimem/memory/session/current.md` | Temporary task scratch space that should not become durable memory. |
| Agent | `.aimem/memory/agents/<agent>.md` | Durable facts for a specific agent; committed but not injected by default. |
| User | `~/.aimem/memory/user.md` | Personal memory that follows you across projects when enabled. |

Good memory candidates are stable, validated, reusable, and specific enough for a future
agent to act on. Examples include validation commands, architecture constraints,
dependency rules, naming conventions, release steps, repeated mistakes, and decisions.

During a session, the active coding agent watches for confirmed root causes and fixes,
reusable diagnostic workflows, verified commands, recurring constraints, and corrected
repository rules. After a completed agent turn, the generated `Stop` hook requests one
review turn using the `lesson-learning` skill. The skill can automatically add or update
concise project memory for high-confidence lessons and can update user-owned Copilot
instructions or Kiro steering when a lesson is also a coding rule. Hook scripts do not
parse or persist transcripts and do not author memory themselves.

High confidence requires an explicit user correction or decision, repeated confirmed
behavior, a successful validation, or strong consistency with repository evidence. User
memory, personal preferences, uncertain claims, and deprecations or deletions still require
explicit approval. Weak or incomplete findings stay in session memory until validated.

Do not memorize secrets, credentials, tokens, private keys, sensitive personal data,
temporary plans, task progress, unvalidated assumptions, one-off implementation details,
or full conversation transcripts. If explicit user instructions conflict with existing
memory, the current request wins and the conflict should be surfaced.

Run `/generate-project-instructions` to analyze established repository practices and create
corresponding, scoped GitHub Copilot instructions and Kiro steering files. The workflow uses
repository evidence, preserves existing user-owned guidance, and applies each platform's native
frontmatter and inclusion rules.

## What gets generated

| Layer | Files |
| --- | --- |
| Canonical memory | `.aimem/memory/project.md`, `.aimem/memory/session/current.md`, `.aimem/memory/agents/<agent>.md`, `~/.aimem/memory/user.md` when enabled |
| Memory metadata index | `.aimem/index/project.json` for reviewable metadata and deterministic retrieval |
| Project-local hook scripts | `.aimem/hooks/*.py`, self-contained and standard-library-only |
| MCP server config | `.vscode/mcp.json` for GitHub Copilot in VS Code, `.kiro/settings/mcp.json` for Kiro |
| Kiro | `.kiro/steering/aimem-memory.md`, seed steering files, memory agents, lesson-learning and instruction-generation skills and prompts, `.kiro/hooks/aimem-memory.kiro.hook` |
| GitHub Copilot | `.github/copilot-instructions.md` managed block, `.github/instructions/aimem-memory.instructions.md`, memory agents, lesson-learning and instruction-generation skills and prompts, `.github/hooks/aimem-memory.json` |
| Cross-tool support | `AGENTS.md` managed block, `.gitignore` managed block, `.aimem/config.json`, `.aimem/manifest.json` |

The Stop review consumes an additional model turn. Copilot uses a small runtime state file
under `.aimem/runtime/` to prevent recursion; failures are fail-open so lesson learning
cannot prevent a session from ending. Copilot's transcript path is used only as opaque event
identity because its file format is not a stable API.

## MCP memory service

`aimem init` adds workspace MCP configuration by default so GitHub Copilot in VS Code,
Kiro, and custom agents can all point at the same local memory service. The generated
server entries launch the Python environment that ran `aimem init`:

```bash
<python> -m aimem mcp-server
```

If you pass `--python-command`, that command is used for MCP as well. Existing generated
configs that still point at bare `python` or `python3` are repaired to the current
interpreter when you rerun `aimem init`.

The MCP server is included in the Python package. If you initialized through `npx`, install
it persistently with:

```bash
python -m pip install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
```

The MCP server uses stdio and resolves the project from `--directory`,
`AIMEM_PROJECT_DIR`, or the current workspace. MCP mode requires the installed Python
package and its runtime dependencies; the generated hook scripts remain stdlib-only and
continue to work without a running server.

The server exposes stable, provider-neutral tools:

```text
memory_search
memory_get
memory_propose
memory_approve
memory_reject
memory_context
memory_handoff
memory_conflicts
```

Tool results use JSON envelopes with `schema_version`, `ok`, `data`, `warnings`, and a
stable `error.code` when something fails. `memory_context` returns budgeted, explainable
context, including the character budget used and entries omitted because of the budget.
Durable writes stay governed: `memory_propose` creates local review state under
`.aimem/proposals/`, and `memory_approve` activates an entry in Markdown plus the sidecar
index. For a validated project lesson, the agent may call both tools consecutively and
report the activation in its final response. Approval-gated categories stop after the
proposal until the user approves them.

When the MCP server starts, it loads the current memory files into a local vector database
at `.aimem/index/vector.json`. `memory_search` queries that local vector database with a
deterministic sparse text vector and ranks entries by cosine similarity, then applies
metadata filters such as scope, kind, priority, validation status, and keywords.

## How memory works after init

- **Read**: MCP `memory_context` and generated hooks provide memory context. Deprecated
  entries are excluded, and context is budgeted or capped with curation reminders.
- **Propose**: MCP `memory_propose` records the exact candidate, scope, and reason before
  any durable activation.
- **Write**: for validated project lessons, generated instructions direct the active agent
  to call `memory_approve` automatically after duplicate and conflict checks. Other durable
  changes wait for explicit approval. Activated entries use lightweight Markdown IDs while
  rich metadata lives in `.aimem/index/`.
- **Manage**: generated scripts can list, filter, export, delete, deprecate, restore,
  migrate, consolidate, and de-duplicate memory entries. MCP tools provide shared
  search, get, handoff, context, and conflict inspection for IDEs and custom agents.
- **Guard**: generated hooks block writes that look like secrets in memory files.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

## License

MIT - see [LICENSE](LICENSE).
