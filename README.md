# aimem

**Project knowledge for AI coding agents, stored in each platform's native files.**

`aimem init` creates a Claude Code project-knowledge skill, Kiro steering, GitHub Copilot
instructions, reusable lesson-learning skills, and project-knowledge agents for a repository.
Agents read and update the same native files your team reviews and commits, without a separate
memory directory, metadata index, proposal store, or session/user memory.

## Why use it

AI coding agents work better when durable repository knowledge is explicit: architecture
decisions, validation commands, conventions, recurring mistakes, and domain terminology.
`aimem` seeds the correct files and tells agents where validated lessons belong:

- Kiro stores project knowledge in `.kiro/steering/*.md`.
- GitHub Copilot stores project knowledge in `.github/copilot-instructions.md` and
  `.github/instructions/*.instructions.md`.
- Claude Code stores project knowledge in `.claude/skills/project-knowledge/`, with a concise
  `SKILL.md` entrypoint and detailed `reference.md` and `examples.md` support files.
- Every provider receives a lesson-learning skill and a project-instruction generation agent.
- Each `init` invocation configures exactly one provider.
- Existing user-authored content and focused instruction files are preserved.

## Quick start

Python 3.10 or newer is required.

```bash
pipx install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init --claude
```

The npm package is a thin launcher for the same Python CLI:

```bash
npx github:kbeaugrand/Agent-Memory-Kit init --claude
```

For CI or scripted setup:

```bash
npx github:kbeaugrand/Agent-Memory-Kit init --claude --no-input -C path/to/project
```

## Usage

```text
aimem --help
aimem --version
aimem init --help

aimem init                         # interactive provider selection
aimem init --claude                # create Claude Code project skills, agent, and hook
aimem init --kiro                  # create Kiro steering, skill, and agent
aimem init --copilot               # create Copilot instructions, skill, and agent
aimem init --claude --no-input     # non-interactive Claude Code setup
aimem init --yes                   # accept the default provider (Claude Code)
aimem init --dry-run               # preview changes without writing
aimem init -C path/to/project      # initialize a specific directory
```

Run `init` once per provider when a repository uses several platforms:

```bash
aimem init --claude
aimem init --copilot
```

## Generated files

| Provider | Files |
| --- | --- |
| Kiro | `.kiro/steering/product.md`, `tech.md`, `structure.md`; `.kiro/skills/lesson-learning/SKILL.md`; `.kiro/agents/generate-project-instructions.md`; `.kiro/hooks/lesson-learning.kiro.hook` |
| GitHub Copilot | `.github/copilot-instructions.md`; `.github/skills/lesson-learning/SKILL.md`; `.github/agents/generate-project-instructions.agent.md`; `.github/hooks/lesson-learning.json` |
| Claude Code | `.claude/skills/project-knowledge/{SKILL.md,reference.md,examples.md}`; `.claude/skills/lesson-learning/SKILL.md`; `.claude/agents/generate-project-instructions.md`; `.claude/settings.json` |

Kiro steering files, skills, agents, and detailed provider customizations are seeded once and then
left under user ownership. The aimem block in `.github/copilot-instructions.md` is marker-managed,
so content outside it survives reruns. Claude skill files are seeded once, and Claude hooks are
merged into `.claude/settings.json` without replacing existing settings or hooks.

Invoke the `lesson-learning` skill to extract validated lessons from completed work. Select the
`generate-project-instructions` custom agent to analyze repository practices and create scoped
native guidance on demand.

The generated `Stop` hooks steer the agent toward lesson learning as it finishes. Kiro appends an
agent prompt and relies on normal skill matching to activate `lesson-learning`; it does not call a
skill API directly. Copilot has no documented hook API for invoking a skill, so its command hook
outputs context asking the agent to apply the skill through normal skill matching.
Claude Code uses its native prompt-based `Stop` hook to continue only when a validated lesson still
needs to be recorded.

## Knowledge policy

Generated guidance tells agents to retain only validated, reusable, durable repository facts.
Kiro lessons are added to the owning steering file or a focused steering file. Copilot lessons
are added outside the managed block or to a focused `.instructions.md` file with suitable
`applyTo` frontmatter. Claude lessons are organized by concern in the project-knowledge skill's
`reference.md`; focused cases go in `examples.md` only when they clarify how to apply a lesson.
After completed work, the generated guidance directs agents to invoke the `lesson-learning` skill
when a validated, reusable lesson may have emerged.

Secrets, credentials, personal data, temporary plans, task progress, unvalidated assumptions,
one-off details, and conversation transcripts do not belong in these files. Current explicit
user instructions take precedence over stored project guidance.

## Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
python scripts/check_version_sync.py
```

## License

MIT - see [LICENSE](LICENSE).
