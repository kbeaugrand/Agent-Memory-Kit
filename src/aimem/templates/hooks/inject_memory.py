#!/usr/bin/env python3
"""Inject canonical AI memory into an agent's context at session start.

Modes:
  --format text     Print memory to stdout (used by Kiro command hooks, whose stdout is
                    added to context on SessionStart / UserPromptSubmit).
  --format copilot  Print a VS Code hook JSON object on stdout with
                    ``hookSpecificOutput.additionalContext`` (used by Copilot SessionStart).

This script depends only on the standard library and does not import the ``aimem`` package.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

_LABELS = {
    "project": "PROJECT MEMORY",
    "user": "USER MEMORY",
    "session": "SESSION MEMORY",
}


def build_context(config: dict) -> str:
    parts = []
    for scope in _common.SCOPES:
        if not _common.scope_enabled(config, scope):
            continue
        text = _common.read_text(_common.scope_path(config, scope))
        if not text:
            continue
        cleaned = _common.strip_comments(text).strip()
        if not _common.has_content(cleaned):
            continue
        rel = _common.scope_config(config, scope).get("path", "")
        parts.append("----- {0} ({1}) -----\n{2}".format(_LABELS[scope], rel, cleaned))
    if not parts:
        return ""
    header = (
        "AI MEMORY (injected by aimem). Treat as durable project context; "
        "the current explicit user request comes first.\n\n"
    )
    return header + "\n\n".join(parts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inject AI memory into agent context.")
    parser.add_argument("--format", choices=("text", "copilot"), default="text")
    parser.add_argument("--event", default="SessionStart")
    args = parser.parse_args(argv)

    # Copilot passes a JSON event object on stdin; we do not need it, but drain it so the
    # hook process never blocks waiting on the pipe.
    if args.format == "copilot" and not sys.stdin.isatty():
        try:
            sys.stdin.read()
        except (OSError, ValueError):
            pass

    context = build_context(_common.load_config())

    if args.format == "copilot":
        if context:
            payload = {
                "hookSpecificOutput": {
                    "hookEventName": args.event,
                    "additionalContext": context,
                }
            }
        else:
            payload = {}
        sys.stdout.write(json.dumps(payload))
    elif context:
        sys.stdout.write(context + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
