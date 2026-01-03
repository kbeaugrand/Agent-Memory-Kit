#!/usr/bin/env python3
"""List, delete, deprecate, or restore individual AI memory entries.

Entries are addressed by (scope, section, index), where ``index`` is the 1-based position
of a bullet within its ``## Section``. Deprecation is a reversible soft-delete: the entry
stays in the file (marked) but is excluded from injected context until restored or purged.

Examples:
  python3 manage_memory.py list
  python3 manage_memory.py list --scope project --section Commands
  python3 manage_memory.py delete --scope project --section Commands --index 2
  python3 manage_memory.py delete --scope project --match "old note"
  python3 manage_memory.py deprecate --scope project --section Gotchas --index 1
  python3 manage_memory.py restore --scope project --section Gotchas --index 1
  python3 manage_memory.py list --scope agent --agent Dev

This script depends only on the standard library.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

_CHOICES = ("project", "user", "session", "agent")


def _resolve_path(config: dict, scope: str, agent):
    if scope == "agent":
        if not agent:
            sys.stderr.write("aimem: --agent is required for --scope agent\n")
            return None
        return _common.agent_memory_path(config, agent)
    return _common.scope_path(config, scope)


def _iter_targets(config: dict, scope, agent):
    """Yield ``(label, path)`` for the requested scope, or all enabled scopes if none."""
    if scope:
        if scope == "agent" and not agent:
            for name, path in _common.list_agent_files(config):
                yield ("agent:" + name, path)
            return
        path = _resolve_path(config, scope, agent)
        if path:
            label = scope if scope != "agent" else "agent:" + _common.sanitize_agent(agent)
            yield (label, path)
        return
    for canonical in _common.SCOPES:
        if _common.scope_enabled(config, canonical):
            yield (canonical, _common.scope_path(config, canonical))
    if _common.scope_enabled(config, "agent"):
        for name, path in _common.list_agent_files(config):
            yield ("agent:" + name, path)


def _rel(path: str) -> str:
    try:
        return os.path.relpath(path, _common.project_root())
    except ValueError:
        return path


def _cmd_list(config: dict, args) -> int:
    marker = _common.deprecation_marker(config)
    any_rows = False
    for label, path in _iter_targets(config, args.scope, args.agent):
        entries = _common.list_entries(_common.read_text(path))
        if args.section:
            entries = [item for item in entries if item[0] == args.section]
        if not entries:
            continue
        any_rows = True
        sys.stdout.write("# {0} ({1})\n".format(label, _rel(path)))
        current = None
        for section, index, deprecated, body in entries:
            if section != current:
                sys.stdout.write("## {0}\n".format(section))
                current = section
            flag = " {0}".format(marker) if deprecated else ""
            sys.stdout.write("  [{0}]{1} {2}\n".format(index, flag, body))
        sys.stdout.write("\n")
    if not any_rows:
        sys.stdout.write("aimem: no matching memory entries.\n")
    return 0


def _find_match(text: str, needle: str):
    lowered = needle.lower()
    for section, index, _deprecated, body in _common.list_entries(text):
        if lowered in body.lower():
            return section, index
    return None, None


def _cmd_mutate(config: dict, args, action: str) -> int:
    path = _resolve_path(config, args.scope, args.agent)
    if path is None:
        return 2
    text = _common.read_text(path)
    if not text.strip():
        sys.stderr.write("aimem: no memory found at {0}\n".format(path))
        return 2

    section, index = args.section, args.index
    if action == "delete" and getattr(args, "match", None):
        section, index = _find_match(text, args.match)
        if section is None:
            sys.stderr.write("aimem: no entry matching '{0}'\n".format(args.match))
            return 2
    if section is None or index is None:
        sys.stderr.write("aimem: --section and --index (or --match for delete) are required\n")
        return 2

    marker = _common.deprecation_marker(config)
    if action == "delete":
        updated, ok = _common.delete_entry(text, section, index)
    elif action == "deprecate":
        updated, ok = _common.set_deprecated(text, section, index, True, marker)
    else:  # restore
        updated, ok = _common.set_deprecated(text, section, index, False, marker)

    if not ok:
        sys.stderr.write("aimem: no entry at section '{0}' index {1}\n".format(section, index))
        return 2
    _common.atomic_write(path, updated)
    sys.stdout.write("aimem: {0}d '{1}' #{2} in {3}\n".format(action, section, index, _rel(path)))
    return 0


def _add_target_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--scope", choices=_CHOICES, required=True)
    sub.add_argument("--agent", help="Agent name (required for --scope agent).")
    sub.add_argument("--section", help="Section heading (without the leading '## ').")
    sub.add_argument("--index", type=int, help="1-based bullet position within the section.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Manage individual AI memory entries.")
    subparsers = parser.add_subparsers(dest="command")

    p_list = subparsers.add_parser("list", help="List memory entries with their addresses.")
    p_list.add_argument("--scope", choices=_CHOICES)
    p_list.add_argument("--agent")
    p_list.add_argument("--section")

    p_delete = subparsers.add_parser("delete", help="Permanently remove an entry.")
    _add_target_args(p_delete)
    p_delete.add_argument("--match", help="Delete the first entry whose text contains this.")

    p_deprecate = subparsers.add_parser("deprecate", help="Soft-delete (mark) an entry.")
    _add_target_args(p_deprecate)

    p_restore = subparsers.add_parser("restore", help="Un-deprecate a previously marked entry.")
    _add_target_args(p_restore)

    args = parser.parse_args(argv)
    config = _common.load_config()

    if args.command == "list":
        return _cmd_list(config, args)
    if args.command in ("delete", "deprecate", "restore"):
        return _cmd_mutate(config, args, args.command)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
