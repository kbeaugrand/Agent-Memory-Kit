#!/usr/bin/env python3
"""Record durable AI memory into a scope, safely and idempotently.

Usage:
  python3 record_memory.py --scope project --topic "Commands" --text "Run tests with pytest"

The entry is redacted of obvious secrets, de-duplicated within its section, written as
readable Markdown, and indexed with full sidecar metadata. This script depends only on
the standard library.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

_TITLES = {"project": "Project Memory", "user": "User Memory", "session": "Session Memory"}


def _split_values(values: list) -> list:
    result = []
    for raw in values:
        for item in raw.split(","):
            value = item.strip()
            if value:
                result.append(value)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Record a fact into AI memory.")
    parser.add_argument("--scope", required=True, choices=(*_common.SCOPES, "agent"))
    parser.add_argument("--agent", help="Agent name (required for --scope agent).")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--kind", choices=_common.MEMORY_RECORD_KINDS, default="fact")
    parser.add_argument("--status", choices=_common.MEMORY_RECORD_STATUSES, default="active")
    parser.add_argument("--priority", choices=_common.MEMORY_PRIORITIES, default="medium")
    parser.add_argument(
        "--evidence",
        action="append",
        choices=_common.MEMORY_EVIDENCE_LEVELS,
        default=[],
        help="Evidence level; may be supplied multiple times.",
    )
    parser.add_argument(
        "--validation-status",
        choices=_common.MEMORY_VALIDATION_STATUSES,
        default="needs_review",
    )
    parser.add_argument("--source", default="manual")
    parser.add_argument(
        "--verified-from",
        action="append",
        default=[],
        help="Human-readable source path that verifies the memory; may be repeated.",
    )
    parser.add_argument("--confidence", type=float, default=0.8)
    parser.add_argument("--valid-from")
    parser.add_argument("--valid-until")
    parser.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Search keyword; may be repeated or comma-separated.",
    )
    parser.add_argument(
        "--relationship",
        action="append",
        default=[],
        help="Relationship as TYPE:ID; may be supplied multiple times.",
    )
    parser.add_argument(
        "--related",
        action="append",
        default=[],
        help="Related memory id; stored as a relates_to relationship.",
    )
    parser.add_argument("--reason", default="")
    parser.add_argument("--impact", default="")
    parser.add_argument(
        "--alternative",
        action="append",
        default=[],
        help="Decision alternative; may be repeated or comma-separated.",
    )
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="Prefix the visible entry text with a UTC timestamp.",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Compatibility no-op; visible timestamps are opt-in with --timestamp.",
    )
    args = parser.parse_args(argv)

    config = _common.load_config()
    if not _common.scope_enabled(config, args.scope):
        sys.stderr.write("aimem: scope '{0}' is not enabled in .aimem/config.json\n".format(args.scope))
        return 2

    if args.scope == "agent":
        if not args.agent:
            sys.stderr.write("aimem: --agent is required for --scope agent\n")
            return 2
        path = _common.agent_memory_path(config, args.agent)
        title = "Agent Memory: {0}".format(_common.sanitize_agent(args.agent))
    else:
        path = _common.scope_path(config, args.scope)
        title = _TITLES[args.scope]

    compiled = _common.compile_redactions(config)
    text, redacted = _common.redact(args.text.strip(), compiled)
    if redacted:
        sys.stderr.write("aimem: a secret was detected and redacted before recording.\n")
    if not text:
        sys.stderr.write("aimem: refusing to record an empty entry.\n")
        return 2

    relationships = []
    for raw in args.relationship:
        if ":" not in raw:
            sys.stderr.write("aimem: --relationship must use TYPE:ID format\n")
            return 2
        rel_type, rel_id = raw.split(":", 1)
        relationships.append({"type": rel_type.strip(), "id": rel_id.strip()})
    for rel_id in _split_values(args.related):
        relationships.append({"type": "relates_to", "id": rel_id})

    topic = args.topic.strip()
    validation_status = args.validation_status
    if args.status == "deprecated" and validation_status == "needs_review":
        validation_status = "deprecated"
    record_id = _common.stable_record_id(args.scope, topic, args.kind, text)
    existing_record = _common.get_index_record(config, args.scope, record_id)

    try:
        record = existing_record or _common.make_record(
            args.scope,
            args.kind,
            args.status,
            args.source.strip(),
            args.confidence,
            args.valid_from,
            args.valid_until,
            relationships,
            record_id=record_id,
            section=topic,
            text=text,
            priority=args.priority,
            evidence=args.evidence or ["agent_inferred"],
            validation_status=validation_status,
            verified_from=_split_values(args.verified_from),
            keywords=_split_values(args.keyword),
            agent=args.agent or "",
            reason=args.reason.strip(),
            impact=args.impact.strip(),
            alternatives=_split_values(args.alternative),
        )
    except ValueError as exc:
        sys.stderr.write("aimem: invalid memory record: {0}\n".format(exc))
        return 2

    entry_text = "[{0}] {1}".format(record["created_at"], text) if args.timestamp else text
    entry = _common.format_memory_entry(entry_text, record)

    existing = _common.read_text(path)
    if not existing.strip():
        existing = "# {0}\n\n".format(title)

    updated = _common.add_entry(existing, topic, entry)
    _common.atomic_write(path, updated)
    if existing_record is None:
        _common.upsert_index_record(config, record)

    warn_limit = int(config.get("memory", {}).get("warn_entries_per_section", 50))
    active = _common.count_active_entries(updated, topic)
    if warn_limit and active > warn_limit:
        sys.stderr.write(
            "aimem: section '{0}' now holds {1} active entries (> {2}); consider curating with "
            "the memory-curator agent or manage_memory.py.\n".format(topic, active, warn_limit)
        )

    sys.stdout.write("aimem: recorded to {0} under '{1}'.\n".format(path, topic))
    return 0


if __name__ == "__main__":
    sys.exit(main())
