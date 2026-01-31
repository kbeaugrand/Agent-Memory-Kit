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

    toolchains = parser.add_argument_group("toolchains")
    toolchains.add_argument("--kiro", action="store_true", help="Generate Kiro artifacts.")
    toolchains.add_argument(
        "--copilot", action="store_true", help="Generate GitHub Copilot artifacts."
    )
    toolchains.add_argument(
        "--both", action="store_true", help="Generate both Kiro and Copilot artifacts."
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Accept defaults without prompting (implies both toolchains).",
    )
    parser.add_argument(
        "--no-input", action="store_true", help="Never prompt; use defaults (for CI)."
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

    kiro, copilot = _select_toolchains(args, interactive)
    if not kiro and not copilot:
        print("aimem: nothing to do — no toolchains selected.")
        return 1
    plan = _build_plan(root, kiro=kiro, copilot=copilot)

    results = []
    for planned in plan:
        result = apply_file(planned, dry_run=args.dry_run)
        results.append(result)

    changed = any(r.action in {Action.CREATED, Action.UPDATED} for r in results)
    _print_summary(
        results,
        env=env,
        kiro=kiro,
        copilot=copilot,
        dry_run=args.dry_run,
        changed=changed,
    )
    return 0


def _select_toolchains(args: argparse.Namespace, interactive: bool) -> tuple[bool, bool]:
    if args.kiro or args.copilot or args.both:
        return (bool(args.both or args.kiro), bool(args.both or args.copilot))
    if interactive:
        return prompts.select_toolchains()
    return True, True


def _render(relpath: str) -> str:
    return load_template(relpath)


def _build_plan(
    root: Path,
    *,
    kiro: bool,
    copilot: bool,
) -> list[PlannedFile]:
    def project(key: str, mode: WriteMode, content: str, comment_style: str = "md") -> PlannedFile:
        return PlannedFile(
            key=key, path=root / key, mode=mode, content=content, comment_style=comment_style
        )

    plan: list[PlannedFile] = []

    if kiro:
        plan.extend(
            [
                project(
                    paths.KIRO_STEERING_KNOWLEDGE,
                    WriteMode.SEED,
                    _render("kiro/steering_project_knowledge.md"),
                ),
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
                    paths.KIRO_SKILL_GENERATE_PROJECT_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("skills/generate_project_instructions.md"),
                ),
            ]
        )

    if copilot:
        plan.extend(
            [
                project(
                    paths.COPILOT_INSTRUCTIONS,
                    WriteMode.SHARED,
                    _render("copilot/project_knowledge_block.md"),
                ),
                project(
                    paths.COPILOT_KNOWLEDGE_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("copilot/project_knowledge.instructions.md"),
                ),
                project(
                    paths.COPILOT_SKILL_LESSON_LEARNING,
                    WriteMode.SEED,
                    _render("skills/lesson_learning.md"),
                ),
                project(
                    paths.COPILOT_SKILL_GENERATE_PROJECT_INSTRUCTIONS,
                    WriteMode.SEED,
                    _render("skills/generate_project_instructions.md"),
                ),
            ]
        )

    return plan


def _print_summary(
    results: list[FileResult],
    *,
    env: environment.Environment,
    kiro: bool,
    copilot: bool,
    dry_run: bool,
    changed: bool,
) -> None:
    selected = ", ".join(name for name, on in (("Kiro", kiro), ("Copilot", copilot)) if on)
    heading = "aimem init (dry run)" if dry_run else "aimem init"
    print(f"{heading} — {env.root}")
    print(f"Toolchains: {selected}")
    print()

    for result in results:
        symbol = _ACTION_SYMBOL.get(result.action, "?")
        print(f"  {symbol} {result.action.value:<10} {result.key}")

    print()
    if dry_run:
        print("Dry run complete — no files were written.")
        return
    if changed:
        print("Done. Review the generated steering, instruction, and skill files.")
    else:
        print("Already up to date — no changes were necessary.")
    print("Rerun `aimem init` anytime to add missing platform files.")
