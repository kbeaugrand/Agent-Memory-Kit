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
    parser.add_argument("--scope", required=True, choices=_common.SCOPES)
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

    compiled = _common.compile_redactions(config)
    text, redacted = _common.redact(args.text.strip(), compiled)
    if redacted:
        sys.stderr.write("aimem: a secret was detected and redacted before recording.\n")
    if not text:
        sys.stderr.write("aimem: refusing to record an empty entry.\n")
        return 2

    entry = text if args.no_timestamp else "[{0}] {1}".format(_common.now_iso(), text)

    path = _common.scope_path(config, args.scope)
    existing = _common.read_text(path)
    if not existing.strip():
        existing = "# {0}\n\n".format(_TITLES[args.scope])

    updated = _common.add_entry(existing, args.topic.strip(), entry)
    _common.atomic_write(path, updated)
    sys.stdout.write("aimem: recorded to {0} under '{1}'.\n".format(path, args.topic.strip()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
