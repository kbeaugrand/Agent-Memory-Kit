"""``aimem init`` — initialize or update AI memory configuration for a project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aimem.core import environment, paths, prompts
from aimem.core.writer import Action, FileResult, PlannedFile, WriteMode, apply_file
from aimem.templates.loader import load_template

_ACTION_SYMBOL = {
    Action.CREATED: "+",
    Action.UPDATED: "~",
    Action.UNCHANGED: "=",
    Action.SKIPPED: ".",
}


def add_init_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the options for ``aimem init``."""
    parser.add_argument(
        "-C",
        "--directory",
        default=".",
        metavar="PATH",
        help="Target project directory (default: current directory).",
    )

    providers = parser.add_mutually_exclusive_group()
    providers.add_argument("--kiro", action="store_true", help="Generate Kiro artifacts.")
    providers.add_argument(
        "--copilot", action="store_true", help="Generate GitHub Copilot artifacts."
    )
    providers.add_argument("--claude", action="store_true", help="Generate Claude Code artifacts.")

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Accept the default provider without prompting.",
    )
    parser.add_argument(
        "--no-input", action="store_true", help="Never prompt; requires a provider (for CI)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )


def run_init(args: argparse.Namespace) -> int:
    """Execute the initialization/update and return a process exit code."""
    root = Path(args.directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    env = environment.detect(root)

    interactive = sys.stdin.isatty() and not args.no_input and not args.yes

    provider = _select_provider(args, interactive)
    if provider is None:
        print("aimem: specify exactly one provider: --kiro, --copilot, or --claude.")
        return 1
    plan = _build_plan(root, provider=provider)

    results = []
    for planned in plan:
        result = apply_file(planned, dry_run=args.dry_run)
        results.append(result)

    changed = any(r.action in {Action.CREATED, Action.UPDATED} for r in results)
    _print_summary(
        results,
        env=env,
        provider=provider,
        dry_run=args.dry_run,
        changed=changed,
    )
    return 0


def _select_provider(args: argparse.Namespace, interactive: bool) -> str | None:
    if args.kiro:
        return "kiro"
    if args.copilot:
        return "copilot"
    if args.claude:
        return "claude"
    if interactive:
        return prompts.select_provider()
    if args.yes:
        return "claude"
    return None


def _render(relpath: str) -> str:
    return load_template(relpath)


def _build_plan(
    root: Path,
    *,
    provider: str,
) -> list[PlannedFile]:
    def project(key: str, mode: WriteMode, content: str, comment_style: str = "md") -> PlannedFile:
        return PlannedFile(
            key=key, path=root / key, mode=mode, content=content, comment_style=comment_style
        )

    plan: list[PlannedFile] = []

    if provider == "kiro":
        plan.extend(
            [
                project(
                    paths.KIRO_STEERING_PRODUCT,
                    WriteMode.SEED,
                    _render("kiro/steering_product.md"),
                ),
                project(
                    paths.KIRO_STEERING_TECH,
                    WriteMode.SEED,
                    _render("kiro/steering_tech.md"),
                ),
                project(
                    paths.KIRO_STEERING_STRUCTURE,
                    WriteMode.SEED,
                    _render("kiro/steering_structure.md"),
                ),
                project(
                    paths.KIRO_SKILL_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("skills/lesson_learning.md"),
                ),
                project(
                    paths.KIRO_AGENT_GENERATE_PROJECT_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("agents/kiro_generate_project_instructions.md"),
                ),
                project(
                    paths.KIRO_HOOK_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("hooks/kiro_lesson_learning.json"),
                ),
            ]
        )

    if provider == "copilot":
        plan.extend(
            [
                project(
                    paths.COPILOT_INSTRUCTIONS,
                    WriteMode.SHARED,
                    _render("copilot/project_knowledge_block.md"),
                ),
                project(
                    paths.COPILOT_SKILL_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("skills/lesson_learning.md"),
                ),
                project(
                    paths.COPILOT_AGENT_GENERATE_PROJECT_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("agents/copilot_generate_project_instructions.md"),
                ),
                project(
                    paths.COPILOT_HOOK_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("hooks/copilot_lesson_learning.json"),
                ),
            ]
        )

    if provider == "claude":
        plan.extend(
            [
                project(
                    paths.CLAUDE_SKILL_PROJECT_KNOWLEDGE,
                    WriteMode.SEED,
                    _render("claude/project_knowledge_skill.md"),
                ),
                project(
                    paths.CLAUDE_SKILL_PROJECT_KNOWLEDGE_REFERENCE,
                    WriteMode.SEED,
                    _render("claude/project_knowledge_reference.md"),
                ),
                project(
                    paths.CLAUDE_SKILL_PROJECT_KNOWLEDGE_EXAMPLES,
                    WriteMode.SEED,
                    _render("claude/project_knowledge_examples.md"),
                ),
                project(
                    paths.CLAUDE_SKILL_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("claude/lesson_learning.md"),
                ),
                project(
                    paths.CLAUDE_AGENT_GENERATE_PROJECT_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("agents/claude_generate_project_instructions.md"),
                ),
                project(
                    paths.CLAUDE_SETTINGS,
                    WriteMode.JSON_MERGE,
                    _render("hooks/claude_lesson_learning.json"),
                ),
            ]
        )

    return plan


def _print_summary(
    results: list[FileResult],
    *,
    env: environment.Environment,
    provider: str,
    dry_run: bool,
    changed: bool,
) -> None:
    selected = {"kiro": "Kiro", "copilot": "Copilot", "claude": "Claude Code"}[provider]
    heading = "aimem init (dry run)" if dry_run else "aimem init"
    print(f"{heading} — {env.root}")
    print(f"Provider: {selected}")
    print()

    for result in results:
        symbol = _ACTION_SYMBOL.get(result.action, "?")
        print(f"  {symbol} {result.action.value:<10} {result.key}")

    print()
    if dry_run:
        print("Dry run complete — no files were written.")
        return
    if changed:
        print("Done. Review the generated provider-native project knowledge files.")
    else:
        print("Already up to date — no changes were necessary.")
    print("Rerun `aimem init` anytime to add missing platform files.")
