#!/usr/bin/env python3
"""Record a durable fact into a memory scope, safely and idempotently.

Usage:
  python3 record_memory.py --scope project --topic "Commands" --text "Run tests with pytest"

The entry is redacted of obvious secrets, timestamped, de-duplicated within its section,
and written atomically. This script depends only on the standard library.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

_TITLES = {"project": "Project Memory", "user": "User Memory", "session": "Session Memory"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Record a fact into AI memory.")
    parser.add_argument("--scope", required=True, choices=(*_common.SCOPES, "agent"))
    parser.add_argument("--agent", help="Agent name (required for --scope agent).")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Do not prefix the entry with a UTC timestamp.",
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

    entry = text if args.no_timestamp else "[{0}] {1}".format(_common.now_iso(), text)

    topic = args.topic.strip()
    existing = _common.read_text(path)
    if not existing.strip():
        existing = "# {0}\n\n".format(title)

    updated = _common.add_entry(existing, topic, entry)
    _common.atomic_write(path, updated)

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
