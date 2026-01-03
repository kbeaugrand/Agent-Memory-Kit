#!/usr/bin/env python3
"""Normalize, de-duplicate, and redact the canonical memory files.

Runs after memory files change:
  * Kiro:    PostFileSave command hook (matched to .aimem/memory/*.md).
  * Copilot: PostToolUse command hook. Because VS Code currently ignores hook matchers,
             this script self-filters: in ``--mode copilot`` it inspects the tool input
             from stdin and does nothing unless a memory file was touched.

Depends only on the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402


def _stdin_json() -> dict:
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _touched_memory(payload: dict) -> bool:
    blob = json.dumps(payload).lower()
    return ".aimem/memory" in blob or ".aimem\\\\memory" in blob


def consolidate_all(config: dict) -> int:
    max_entries = int(config.get("memory", {}).get("max_entries_per_section", 200))
    marker = _common.deprecation_marker(config)
    compiled = _common.compile_redactions(config)
    changed = 0

    targets = [
        _common.scope_path(config, scope)
        for scope in _common.SCOPES
        if _common.scope_enabled(config, scope)
    ]
    if _common.scope_enabled(config, "agent"):
        targets.extend(path for _name, path in _common.list_agent_files(config))

    for path in targets:
        original = _common.read_text(path)
        if not original:
            continue
        updated = _common.consolidate(original, max_entries, compiled, marker)
        if updated != original:
            _common.atomic_write(path, updated)
            changed += 1
    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Consolidate AI memory files.")
    parser.add_argument("--mode", choices=("text", "kiro", "copilot"), default="text")
    args = parser.parse_args(argv)

    if args.mode == "copilot":
        payload = _stdin_json()
        if not _touched_memory(payload):
            sys.stdout.write("{}")
            return 0

    consolidate_all(_common.load_config())

    if args.mode == "copilot":
        sys.stdout.write("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
