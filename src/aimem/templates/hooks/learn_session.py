"""Coordinate one lesson-learning turn after each completed Copilot agent turn.

The Stop transcript is deliberately treated as an opaque event identity. Its format is
not a stable API, so this hook never reads or copies its contents.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from _common import aimem_dir, atomic_write, read_text

_STATE_PATH = os.path.join(aimem_dir(), "runtime", "lesson-learning.json")
_REASON = (
    "Invoke the lesson-learning skill now. Review the completed conversation in the current "
    "context, record any high-confidence durable lessons, and create or update user-owned "
    "coding instructions or steering when a lesson is also a prescriptive coding rule. If "
    "nothing durable emerged, make no changes and finish."
)


def _stdin_json() -> dict:
    try:
        raw = sys.stdin.read()
        value = json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_state() -> dict:
    try:
        value = json.loads(read_text(_STATE_PATH))
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _save_state(state: dict) -> None:
    atomic_write(_STATE_PATH, json.dumps(state, indent=2, sort_keys=True) + "\n")


def _fingerprint(path: str) -> str:
    try:
        stat = os.stat(path)
    except OSError:
        return ""
    return "{}:{}".format(stat.st_size, getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1e9)))


def coordinate(payload: dict) -> dict:
    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    if not isinstance(session_id, str) or not session_id.strip():
        return {}
    if not isinstance(transcript_path, str) or not transcript_path.strip():
        return {}

    fingerprint = _fingerprint(transcript_path)
    if not fingerprint:
        return {}

    state = _load_state()
    sessions = state.get("sessions")
    if not isinstance(sessions, dict):
        sessions = {}
    current = sessions.get(session_id)
    if not isinstance(current, dict):
        current = {}

    if current.get("phase") == "pending":
        sessions[session_id] = {"phase": "processed", "fingerprint": fingerprint}
        state["sessions"] = sessions
        _save_state(state)
        return {}

    if current.get("phase") == "processed" and current.get("fingerprint") == fingerprint:
        return {}

    sessions[session_id] = {"phase": "pending", "fingerprint": fingerprint}
    state["sessions"] = sessions
    _save_state(state)
    return {"decision": "block", "reason": _REASON}


def cleanup() -> int:
    try:
        os.remove(_STATE_PATH)
    except FileNotFoundError:
        pass
    except OSError:
        return 0
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()
    if args.cleanup:
        return cleanup()
    try:
        output = coordinate(_stdin_json())
    except (OSError, ValueError, TypeError):
        output = {}
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())