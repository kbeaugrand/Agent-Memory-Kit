# aimem

**Project knowledge for AI coding agents, stored in each platform's native files.**

`aimem init` creates Kiro steering, GitHub Copilot instructions, and reusable skills for a
repository.
Agents read and update the same native files your team reviews and commits, without a separate
memory directory, metadata index, proposal store, or session/user memory.

## Why use it

AI coding agents work better when durable repository knowledge is explicit: architecture
decisions, validation commands, conventions, recurring mistakes, and domain terminology.
`aimem` seeds the correct files and tells agents where validated lessons belong:

- Kiro stores project knowledge in `.kiro/steering/*.md`.
- GitHub Copilot stores project knowledge in `.github/copilot-instructions.md` and
  `.github/instructions/*.instructions.md`.
- Both platforms receive lesson-learning and project-instruction generation skills.
- Toolchain selection controls which files are created.
- Existing user-authored content and focused instruction files are preserved.

## Quick start

Python 3.10 or newer is required.

```bash
pipx install git+https://github.com/kbeaugrand/Agent-Memory-Kit.git
aimem init --both
```

The npm package is a thin launcher for the same Python CLI:

```bash
npx github:kbeaugrand/Agent-Memory-Kit init --both
```

For CI or scripted setup:

```bash
npx github:kbeaugrand/Agent-Memory-Kit init --both --no-input -C path/to/project
```

## Usage

```text
aimem --help
aimem --version
aimem init --help

aimem init                         # interactive toolchain selection
aimem init --both                  # create Kiro and Copilot files
aimem init --kiro                  # create Kiro steering and skills
aimem init --copilot               # create Copilot instructions and skills
aimem init --both --no-input       # non-interactive setup
aimem init --yes                   # accept defaults; implies both toolchains
aimem init --dry-run               # preview changes without writing
aimem init -C path/to/project      # initialize a specific directory
```

## Generated files

| Toolchain | Files |
| --- | --- |
| Kiro | `.kiro/steering/aimem-memory.md`, `product.md`, `tech.md`, `structure.md`; `.kiro/skills/lesson-learning/SKILL.md`, `.kiro/skills/generate-project-instructions/SKILL.md`; `.kiro/hooks/lesson-learning.json` |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/aimem-memory.instructions.md`; `.github/skills/lesson-learning/SKILL.md`, `.github/skills/generate-project-instructions/SKILL.md`; `.github/hooks/lesson-learning.json` |

Kiro steering files, skills, and the detailed Copilot instruction file are seeded once and then
left under user ownership. The aimem block in `.github/copilot-instructions.md` is
marker-managed, so content outside that block survives reruns.

Both generated skills are user-invocable. Invoke `lesson-learning` to extract validated lessons
from completed work, or `generate-project-instructions` to analyze repository practices and
create scoped native guidance on demand.

The generated `Stop` hooks steer the agent toward lesson learning as it finishes. Kiro appends an
agent prompt and relies on normal skill matching to activate `lesson-learning`; it does not call a
skill API directly. Copilot has no documented hook API for invoking a skill, so its command hook
outputs context asking the agent to apply the skill through normal skill matching.

## Knowledge policy

Generated guidance tells agents to retain only validated, reusable, durable repository facts.
Kiro lessons are added to the owning steering file or a focused steering file. Copilot lessons
are added outside the managed block or to a focused `.instructions.md` file with suitable
`applyTo` frontmatter. After completed work, the generated guidance directs agents to invoke the
`lesson-learning` skill when a validated, reusable lesson may have emerged. The skill scopes
targeted knowledge to narrow file globs or Kiro file matches, keeping unrelated instructions out
of the active context as the knowledge base grows.

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
