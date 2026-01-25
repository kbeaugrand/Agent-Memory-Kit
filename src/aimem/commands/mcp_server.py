"""``aimem mcp-server`` — expose aimem memory through Model Context Protocol."""

from __future__ import annotations

import argparse
import sys


def add_mcp_server_arguments(parser: argparse.ArgumentParser) -> None:
    """Register the options for ``aimem mcp-server``."""
    parser.add_argument(
        "-C",
        "--directory",
        metavar="PATH",
        help="Project directory containing .aimem/config.json (default: auto-detect).",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP transport to use (default: stdio).",
    )


def run_mcp_server(args: argparse.Namespace) -> int:
    """Start the MCP server and return a process exit code."""
    try:
        from aimem.mcp.server import run_server
    except ImportError as exc:
        print(
            "aimem: MCP server support requires the Python 'mcp' package. "
            "Install aimem with its runtime dependencies and try again.",
            file=sys.stderr,
        )
        print(f"aimem: import error: {exc}", file=sys.stderr)
        return 2

    run_server(directory=args.directory, transport=args.transport)
    return 0