#!/usr/bin/env python3
"""Block writing secrets into memory files before a tool runs (PreToolUse guard).

The guard reads the tool invocation from stdin (JSON) and blocks it only when BOTH:
  * the invocation references a memory file (``.aimem/memory/...``), and
  * the invocation payload contains an obvious secret (per config redaction patterns).

It fails open: if the input cannot be parsed or is ambiguous, the tool is allowed. This
keeps legitimate work unblocked while stopping the clearest secret-leak mistakes.

Modes:
  --mode copilot  Emit VS Code ``hookSpecificOutput.permissionDecision`` JSON (exit 0).
  --mode kiro     Emit a message on stderr and exit 2 to block.

Depends only on the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common  # noqa: E402

_REASON = (
    "aimem guard: refusing to write an apparent secret into a memory file. "
    "Memory is committed and shared — never store secrets, tokens, or passwords."
)


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


def _references_memory(blob: str) -> bool:
    lowered = blob.lower()
    return ".aimem/memory" in lowered or ".aimem\\memory" in lowered


def should_block(payload: dict, compiled) -> bool:
    tool_input = payload.get("tool_input", payload)
    try:
        blob = json.dumps(tool_input)
    except (TypeError, ValueError):
        return False
    if not _references_memory(blob):
        return False
    return _common.contains_secret(blob, compiled)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Guard memory files against secret writes.")
    parser.add_argument("--mode", choices=("kiro", "copilot"), default="copilot")
    args = parser.parse_args(argv)

    payload = _stdin_json()
    compiled = _common.compile_redactions(_common.load_config())
    block = should_block(payload, compiled)

    if args.mode == "copilot":
        if block:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _REASON,
                }
            }
        else:
            output = {}
        sys.stdout.write(json.dumps(output))
        return 0

    # Kiro mode: exit code 2 blocks the tool and returns stderr to the agent.
    if block:
        sys.stderr.write(_REASON + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
