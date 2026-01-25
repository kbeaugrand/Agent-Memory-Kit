#!/usr/bin/env python3
"""List, delete, deprecate, restore, or migrate individual AI memory entries.

Entries are addressed by (scope, section, index), where ``index`` is the 1-based position
of a bullet within its ``## Section``. Deprecation is a reversible soft-delete: the entry
stays in the file (marked) but is excluded from injected context until restored or purged.

Examples:
  python3 manage_memory.py list
  python3 manage_memory.py list --scope project --section Commands
  python3 manage_memory.py delete --scope project --section Commands --index 2
  python3 manage_memory.py delete --scope project --match "old note"
    python3 manage_memory.py deprecate --scope project --section "Common Mistakes" --index 1
    python3 manage_memory.py restore --scope project --section "Common Mistakes" --index 1
  python3 manage_memory.py list --scope agent --agent Dev
    python3 manage_memory.py migrate --scope project

This script depends only on the standard library.
"""

from __future__ import annotations

import argparse
import json
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
    rows = []
    for label, path in _iter_targets(config, args.scope, args.agent):
        scope = label.split(":", 1)[0]
        entries = _common.parsed_entries(
            _common.read_text(path), scope, _common.index_record_map(config, scope)
        )
        if args.section:
            entries = [item for item in entries if item["section"] == args.section]
        if args.id:
            entries = [item for item in entries if item["record"] and item["record"].get("id") == args.id]
        if args.kind:
            entries = [item for item in entries if item["record"] and item["record"].get("kind") == args.kind]
        if args.status:
            entries = [item for item in entries if item["record"] and item["record"].get("status") == args.status]
        if args.priority:
            entries = [item for item in entries if item["record"] and item["record"].get("priority") == args.priority]
        if args.evidence:
            entries = [
                item
                for item in entries
                if item["record"] and args.evidence in item["record"].get("evidence", [])
            ]
        if args.validation_status:
            entries = [
                item
                for item in entries
                if item["record"] and item["record"].get("validation_status") == args.validation_status
            ]
        if args.source:
            entries = [item for item in entries if item["record"] and item["record"].get("source") == args.source]
        if args.verified_from:
            entries = [
                item
                for item in entries
                if item["record"] and args.verified_from in item["record"].get("verified_from", [])
            ]
        if args.keyword:
            needle = args.keyword.lower()
            entries = [
                item
                for item in entries
                if needle in item["text"].lower()
                or (
                    item["record"]
                    and needle in [keyword.lower() for keyword in item["record"].get("keywords", [])]
                )
            ]
        if args.related:
            entries = [
                item
                for item in entries
                if item["record"]
                and any(rel.get("id") == args.related for rel in item["record"].get("relationships", []))
            ]
        if not entries:
            continue
        any_rows = True
        for entry in entries:
            row = dict(entry)
            row["target"] = label
            row["path"] = _rel(path)
            rows.append(row)
        if args.format == "json":
            continue
        sys.stdout.write("# {0} ({1})\n".format(label, _rel(path)))
        current = None
        for entry in entries:
            section, index, deprecated, body = (
                entry["section"],
                entry["index"],
                entry["deprecated"],
                entry["text"],
            )
            if section != current:
                sys.stdout.write("## {0}\n".format(section))
                current = section
            flag = " {0}".format(marker) if deprecated else ""
            record = entry["record"] or {}
            meta = ""
            if record:
                meta = " id={0} kind={1} priority={2} status={3} validation={4} source={5}".format(
                    record.get("id"),
                    record.get("kind"),
                    record.get("priority"),
                    record.get("status"),
                    record.get("validation_status"),
                    record.get("source"),
                )
            sys.stdout.write("  [{0}]{1}{2} {3}\n".format(index, flag, meta, body))
        sys.stdout.write("\n")
    if args.format == "json":
        sys.stdout.write(json.dumps(rows, sort_keys=True) + "\n")
        return 0
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

    records = _common.index_record_map(config, args.scope)
    entries = _common.parsed_entries(text, args.scope, records)
    target = None
    for entry in entries:
        if entry["section"] == section and entry["index"] == index:
            target = entry
            break
    record_id = target.get("id") if target else None

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
    if record_id:
        if action == "delete":
            _common.remove_index_record(config, args.scope, record_id)
        else:
            _common.set_index_deprecated(config, args.scope, record_id, action == "deprecate")
    sys.stdout.write("aimem: {0}d '{1}' #{2} in {3}\n".format(action, section, index, _rel(path)))
    return 0


def _migrate_text(markdown: str, scope: str, source: str) -> "tuple[str, int, list]":
    lines = markdown.split("\n")
    section = ""
    changed = 0
    records = []
    for index, line in enumerate(lines):
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        indent = line[: len(line) - len(line.lstrip())]
        body = stripped[2:]
        if _common.record_id_from_entry(body):
            continue
        visible, record = _common._split_record_comment(body)
        status = "deprecated" if visible.lstrip().startswith(_common.deprecation_marker({})) else "active"
        clean = visible
        if status == "deprecated":
            clean = clean.lstrip()[len(_common.DEPRECATION_MARKER) :].lstrip()
        try:
            if record:
                record = _common.legacy_record_to_v2(record, section, clean, source=None)
            else:
                record = _common.make_record(
                    scope,
                    "fact",
                    status,
                    source,
                    0.5,
                    _common.now_iso(),
                    None,
                    [],
                    _common.migration_record_id(scope, section, clean),
                    section=section,
                    text=clean,
                    priority="medium",
                    evidence=["agent_inferred"],
                    validation_status="deprecated" if status == "deprecated" else "needs_review",
                )
        except ValueError:
            continue
        lines[index] = indent + "- " + _common.attach_record(visible, record)
        records.append(record)
        changed += 1
    text = "\n".join(lines)
    return (text if text.endswith("\n") else text + "\n"), changed, records


def _cmd_migrate(config: dict, args) -> int:
    changed_files = 0
    changed_entries = 0
    for label, path in _iter_targets(config, args.scope, args.agent):
        text = _common.read_text(path)
        if not text.strip():
            continue
        scope = label.split(":", 1)[0]
        updated, count, records = _migrate_text(text, scope, args.source)
        if count:
            changed_entries += count
            changed_files += 1
            if not args.dry_run:
                _common.atomic_write(path, updated)
                for record in records:
                    _common.upsert_index_record(config, record)
            sys.stdout.write("aimem: migrated {0} entries in {1}\n".format(count, _rel(path)))
    if not changed_entries:
        sys.stdout.write("aimem: no legacy memory entries found.\n")
    elif args.dry_run:
        sys.stdout.write("aimem: dry run; no files changed.\n")
    else:
        sys.stdout.write("aimem: migrated {0} entries across {1} files.\n".format(changed_entries, changed_files))
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
    p_list.add_argument("--id")
    p_list.add_argument("--kind", choices=_common.MEMORY_RECORD_KINDS)
    p_list.add_argument("--status", choices=_common.MEMORY_RECORD_STATUSES)
    p_list.add_argument("--priority", choices=_common.MEMORY_PRIORITIES)
    p_list.add_argument("--evidence", choices=_common.MEMORY_EVIDENCE_LEVELS)
    p_list.add_argument("--validation-status", choices=_common.MEMORY_VALIDATION_STATUSES)
    p_list.add_argument("--source")
    p_list.add_argument("--verified-from")
    p_list.add_argument("--keyword")
    p_list.add_argument("--related")
    p_list.add_argument("--format", choices=("text", "json"), default="text")

    p_delete = subparsers.add_parser("delete", help="Permanently remove an entry.")
    _add_target_args(p_delete)
    p_delete.add_argument("--match", help="Delete the first entry whose text contains this.")

    p_deprecate = subparsers.add_parser("deprecate", help="Soft-delete (mark) an entry.")
    _add_target_args(p_deprecate)

    p_restore = subparsers.add_parser("restore", help="Un-deprecate a previously marked entry.")
    _add_target_args(p_restore)

    p_migrate = subparsers.add_parser("migrate", help="Add structured metadata to legacy Markdown bullets.")
    p_migrate.add_argument("--scope", choices=_CHOICES)
    p_migrate.add_argument("--agent")
    p_migrate.add_argument("--source", default="migration")
    p_migrate.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    config = _common.load_config()

    if args.command == "list":
        return _cmd_list(config, args)
    if args.command in ("delete", "deprecate", "restore"):
        return _cmd_mutate(config, args, args.command)
    if args.command == "migrate":
        return _cmd_migrate(config, args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
