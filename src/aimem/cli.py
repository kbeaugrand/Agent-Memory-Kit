"""Command-line interface for aimem."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from aimem import __version__
from aimem.commands.init import add_init_arguments, run_init


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="aimem",
        description=("Initialize native Kiro steering, GitHub Copilot instructions, and skills."),
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"aimem {__version__}",
        help="Show the aimem version and exit.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize native AI project knowledge files and skills.",
        description="Initialize Kiro steering, GitHub Copilot instructions, and skills.",
        allow_abbrev=False,
    )
    add_init_arguments(init_parser)
    init_parser.set_defaults(func=run_init)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "command", None) is None:
        parser.print_help()
        return 2

    func: object = getattr(args, "func", None)
    if not callable(func):  # pragma: no cover - defensive guard
        parser.print_help()
        return 2

    result = func(args)
    return int(result)
