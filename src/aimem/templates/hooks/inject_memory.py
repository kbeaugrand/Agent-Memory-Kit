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

_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_VALIDATION_RANK = {"verified": 0, "needs_review": 1, "deprecated": 2}


def _entry_sort_key(entry: dict):
    record = entry.get("record") or {}
    return (
        _PRIORITY_RANK.get(record.get("priority", "medium"), 99),
        _VALIDATION_RANK.get(record.get("validation_status", "needs_review"), 99),
        entry.get("section", ""),
        entry.get("index", 0),
    )


def _render_entries(entries: list) -> str:
    lines = []
    current = None
    for entry in sorted(entries, key=_entry_sort_key):
        body = _common.strip_comments(entry.get("text", "")).rstrip()
        if not body:
            continue
        section = entry.get("section", "")
        if section and section != current:
            if lines:
                lines.append("")
            lines.append("## " + section)
            current = section
        body_lines = body.split("\n")
        lines.append("- " + body_lines[0].strip())
        lines.extend(line.rstrip() for line in body_lines[1:] if line.rstrip())
    return "\n".join(lines).strip()


def _clean_scope_text(config: dict, scope: str, text: str) -> str:
    """Strip comments and deprecated entries before injection, ranking indexed entries."""
    marker = _common.deprecation_marker(config)
    entries = _common.parsed_entries(text, scope, _common.index_record_map(config, scope))
    active = [entry for entry in entries if not entry["deprecated"]]
    if active:
        return _render_entries(active)
    return _common.strip_deprecated(_common.strip_comments(text), marker).strip()


def _agent_parts(config: dict) -> list:
    """Return the agent memory files to inject, honoring policy and the active-agent env.

    Session hooks do not know which agent is active, so agent memory is injected only when
    ``AIMEM_ACTIVE_AGENT`` names one, or when ``scopes.agent.inject`` is ``"all"``.
    """
    if not _common.scope_enabled(config, "agent"):
        return []
    active = os.environ.get("AIMEM_ACTIVE_AGENT", "").strip()
    files = _common.list_agent_files(config)
    if active:
        safe = _common.sanitize_agent(active)
        return [(name, path) for name, path in files if name == safe]
    if _common.agent_scope_config(config).get("inject", "none") == "all":
        return files
    return []


def build_context(config: dict) -> str:
    parts = []
    for scope in _common.SCOPES:
        if not _common.scope_enabled(config, scope):
            continue
        cleaned = _clean_scope_text(
            config, scope, _common.read_text(_common.scope_path(config, scope))
        )
        if not _common.has_content(cleaned):
            continue
        rel = _common.scope_config(config, scope).get("path", "")
        parts.append("----- {0} ({1}) -----\n{2}".format(_LABELS[scope], rel, cleaned))

    for name, path in _agent_parts(config):
        cleaned = _clean_scope_text(config, "agent", _common.read_text(path))
        if not _common.has_content(cleaned):
            continue
        parts.append("----- AGENT MEMORY: {0} -----\n{1}".format(name, cleaned))

    if not parts:
        return ""
    header = (
        "AI MEMORY (injected by aimem). Treat as durable project context; "
        "the current explicit user request comes first.\n\n"
    )
    body = header + "\n\n".join(parts)

    limit = int(config.get("memory", {}).get("max_injection_chars", 12000))
    if limit and len(body) > limit:
        body += (
            "\n\n(aimem: injected memory is large — {0} chars > {1}. Consider curating with "
            "the memory-curator agent to keep injected context focused.)".format(len(body), limit)
        )
    return body


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
