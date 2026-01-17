"""``aimem init`` — initialize or update AI memory configuration for a project."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from aimem import __version__
from aimem.core import config as config_mod
from aimem.core import environment, paths, prompts, rendering
from aimem.core.manifest import Manifest
from aimem.core.writer import Action, FileResult, PlannedFile, WriteMode, apply_file
from aimem.templates.loader import load_template

_ACTION_SYMBOL = {
    Action.CREATED: "+",
    Action.UPDATED: "~",
    Action.UNCHANGED: "=",
    Action.SKIPPED: ".",
    Action.BACKED_UP: "!",
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

    user = parser.add_mutually_exclusive_group()
    user.add_argument(
        "--user",
        action="store_true",
        help="Also set up global user memory in your home directory.",
    )
    user.add_argument("--no-user", action="store_true", help="Do not set up global user memory.")

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
        "--force",
        action="store_true",
        help="Overwrite managed/seed files even if locally modified (backups are still made).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing any files.",
    )
    parser.add_argument(
        "--python-command",
        metavar="CMD",
        help="Python command embedded in generated hooks (default: python3 or existing config).",
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
    user_scope = _select_user_scope(args, interactive)

    existing_config = config_mod.load_existing_config(root / paths.CONFIG_FILE)
    python_command = _resolve_python_command(args, existing_config)
    variables = _variables(python_command)

    config_doc = config_mod.build_config(
        aimem_version=__version__,
        kiro=kiro,
        copilot=copilot,
        user_scope=user_scope,
        python_command=python_command,
        existing=existing_config,
    )
    config_content = config_mod.dumps(config_doc)

    plan = _build_plan(
        root,
        variables,
        kiro=kiro,
        copilot=copilot,
        user_scope=user_scope,
        config_content=config_content,
    )

    manifest = Manifest.load(root / paths.MANIFEST_FILE)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups_root = root / paths.BACKUPS_DIR

    results = []
    for planned in plan:
        entry = manifest.entry(planned.key)
        result, mode, content_hash = apply_file(
            planned,
            entry,
            template_version=__version__,
            backups_root=backups_root,
            timestamp=timestamp,
            force=args.force,
            dry_run=args.dry_run,
        )
        if content_hash:
            manifest.set_entry(planned.key, mode, content_hash, __version__)
        results.append(result)

    changed = any(r.action in {Action.CREATED, Action.UPDATED, Action.BACKED_UP} for r in results)
    if not args.dry_run and (changed or not (root / paths.MANIFEST_FILE).is_file()):
        manifest.save(
            root / paths.MANIFEST_FILE,
            aimem_version=__version__,
            generated_at=_now_iso(),
        )

    _print_summary(
        results,
        env=env,
        kiro=kiro,
        copilot=copilot,
        user_scope=user_scope,
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


def _select_user_scope(args: argparse.Namespace, interactive: bool) -> bool:
    if args.no_user:
        return False
    if args.user:
        return True
    if interactive:
        return prompts.confirm_user_scope()
    return False


def _resolve_python_command(
    args: argparse.Namespace, existing_config: dict[str, object] | None
) -> str:
    if args.python_command:
        return str(args.python_command)
    if existing_config:
        value = existing_config.get("python_command")
        if isinstance(value, str) and value.strip():
            return value
    return "python3"


def _variables(python_command: str) -> dict[str, str]:
    return {
        "AIMEM_VERSION": __version__,
        "PYTHON_COMMAND": python_command,
        "MEMORY_TEMPLATE": paths.MEMORY_TEMPLATE,
        "PROJECT_MEMORY": paths.PROJECT_MEMORY,
        "SESSION_MEMORY": paths.SESSION_MEMORY,
        "USER_MEMORY": paths.USER_MEMORY,
        "AGENTS_MEMORY_DIR": paths.AGENTS_MEMORY_DIR,
        "HOOKS_DIR": paths.HOOKS_DIR,
    }


def _render(relpath: str, variables: dict[str, str]) -> str:
    return rendering.substitute(load_template(relpath), variables)


def _build_plan(
    root: Path,
    variables: dict[str, str],
    *,
    kiro: bool,
    copilot: bool,
    user_scope: bool,
    config_content: str,
) -> list[PlannedFile]:
    def project(key: str, mode: WriteMode, content: str, comment_style: str = "md") -> PlannedFile:
        return PlannedFile(
            key=key, path=root / key, mode=mode, content=content, comment_style=comment_style
        )

    plan: list[PlannedFile] = [
        project(paths.CONFIG_FILE, WriteMode.MANAGED, config_content),
        project(paths.HOOK_COMMON, WriteMode.MANAGED, _render("hooks/_common.py", variables)),
        project(paths.HOOK_INJECT, WriteMode.MANAGED, _render("hooks/inject_memory.py", variables)),
        project(paths.HOOK_RECORD, WriteMode.MANAGED, _render("hooks/record_memory.py", variables)),
        project(
            paths.HOOK_CONSOLIDATE,
            WriteMode.MANAGED,
            _render("hooks/consolidate_memory.py", variables),
        ),
        project(paths.HOOK_GUARD, WriteMode.MANAGED, _render("hooks/guard_memory.py", variables)),
        project(paths.HOOK_MANAGE, WriteMode.MANAGED, _render("hooks/manage_memory.py", variables)),
        project(paths.MEMORY_TEMPLATE, WriteMode.SEED, _render("memory/TEMPLATE.md", variables)),
        project(paths.PROJECT_MEMORY, WriteMode.SEED, _render("memory/project.md", variables)),
        project(
            paths.SESSION_MEMORY, WriteMode.SEED, _render("memory/session_current.md", variables)
        ),
        project(
            paths.AGENTS_MEMORY_README,
            WriteMode.SEED,
            _render("memory/agents_readme.md", variables),
        ),
        project(paths.AGENTS_FILE, WriteMode.SHARED, _render("shared/agents_block.md", variables)),
        project(
            paths.GITIGNORE_FILE,
            WriteMode.SHARED,
            _render("shared/gitignore_block.txt", variables),
            comment_style="hash",
        ),
    ]

    if user_scope:
        user_path = Path(os.path.expanduser(paths.USER_MEMORY))
        plan.append(
            PlannedFile(
                key=paths.USER_MEMORY,
                path=user_path,
                mode=WriteMode.SEED,
                content=_render("memory/user.md", variables),
            )
        )

    if kiro:
        plan.extend(
            [
                project(
                    paths.KIRO_STEERING_MEMORY,
                    WriteMode.MANAGED,
                    _render("kiro/steering_aimem_memory.md", variables),
                ),
                project(
                    paths.KIRO_STEERING_PRODUCT,
                    WriteMode.SEED,
                    _render("kiro/steering_product.md", variables),
                ),
                project(
                    paths.KIRO_STEERING_TECH,
                    WriteMode.SEED,
                    _render("kiro/steering_tech.md", variables),
                ),
                project(
                    paths.KIRO_STEERING_STRUCTURE,
                    WriteMode.SEED,
                    _render("kiro/steering_structure.md", variables),
                ),
                project(
                    paths.KIRO_AGENT_INITIALIZER,
                    WriteMode.MANAGED,
                    _render("kiro/agent_memory_initializer.md", variables),
                ),
                project(
                    paths.KIRO_AGENT_CURATOR,
                    WriteMode.MANAGED,
                    _render("kiro/agent_memory_curator.md", variables),
                ),
                project(
                    paths.KIRO_HOOK,
                    WriteMode.MANAGED,
                    _render("kiro/hook_aimem_memory.kiro.hook", variables),
                ),
            ]
        )

    if copilot:
        plan.extend(
            [
                project(
                    paths.COPILOT_INSTRUCTIONS,
                    WriteMode.SHARED,
                    _render("copilot/instructions_block.md", variables),
                ),
                project(
                    paths.COPILOT_MEMORY_INSTRUCTIONS,
                    WriteMode.MANAGED,
                    _render("copilot/aimem_memory.instructions.md", variables),
                ),
                project(
                    paths.COPILOT_AGENT_INITIALIZER,
                    WriteMode.MANAGED,
                    _render("copilot/agent_memory_initializer.agent.md", variables),
                ),
                project(
                    paths.COPILOT_AGENT_CURATOR,
                    WriteMode.MANAGED,
                    _render("copilot/agent_memory_curator.agent.md", variables),
                ),
                project(
                    paths.COPILOT_HOOK,
                    WriteMode.MANAGED,
                    _render("copilot/hook_aimem_memory.json", variables),
                ),
            ]
        )

    return plan


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _print_summary(
    results: list[FileResult],
    *,
    env: environment.Environment,
    kiro: bool,
    copilot: bool,
    user_scope: bool,
    dry_run: bool,
    changed: bool,
) -> None:
    selected = ", ".join(name for name, on in (("Kiro", kiro), ("Copilot", copilot)) if on)
    heading = "aimem init (dry run)" if dry_run else "aimem init"
    print(f"{heading} — {env.root}")
    print(f"Toolchains: {selected}" + ("  |  user memory: on" if user_scope else ""))
    print()

    for result in results:
        symbol = _ACTION_SYMBOL.get(result.action, "?")
        print(f"  {symbol} {result.action.value:<10} {result.key}")
        if result.backup is not None:
            print(f"      backup: {result.backup}")

    print()
    if dry_run:
        print("Dry run complete — no files were written.")
        return
    if changed:
        print("Done. Review the generated memory files and commit the changes.")
    else:
        print("Already up to date — no changes were necessary.")
    print("Rerun `aimem init` anytime to repair or update the configuration.")
