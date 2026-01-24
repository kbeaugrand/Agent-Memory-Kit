"""Build and merge the ``.aimem/config.json`` document read by the hook scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aimem.core import paths

CONFIG_SCHEMA_VERSION = 1

# Conservative, case-insensitive patterns used by the guard/consolidate hook scripts to
# avoid persisting secrets into memory. Users may extend this list in config.json.
DEFAULT_REDACTION_PATTERNS: list[str] = [
    r"(?i)\b(api[_-]?key|secret|password|passwd|token|client[_-]?secret)\b\s*[:=]\s*\S+",
    r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}",
    r"(?i)\bAKIA[0-9A-Z]{16}\b",
    r"(?i)\bghp_[A-Za-z0-9]{20,}\b",
    r"(?i)\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
]

DEFAULT_MAX_ENTRIES_PER_SECTION = 200
DEFAULT_WARN_ENTRIES_PER_SECTION = 50
DEFAULT_MAX_INJECTION_CHARS = 12000
DEFAULT_DEPRECATION_MARKER = "[DEPRECATED]"


def build_config(
    *,
    aimem_version: str,
    kiro: bool,
    copilot: bool,
    user_scope: bool,
    python_command: str,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce the config document, merging user-editable fields from ``existing``."""
    prior = existing or {}
    prior_memory = prior.get("memory", {}) if isinstance(prior.get("memory"), dict) else {}

    redaction = prior_memory.get("redaction_patterns")
    if not isinstance(redaction, list) or not redaction:
        redaction = list(DEFAULT_REDACTION_PATTERNS)

    max_entries = prior_memory.get("max_entries_per_section")
    if not isinstance(max_entries, int) or max_entries <= 0:
        max_entries = DEFAULT_MAX_ENTRIES_PER_SECTION

    warn_entries = prior_memory.get("warn_entries_per_section")
    if not isinstance(warn_entries, int) or warn_entries <= 0:
        warn_entries = DEFAULT_WARN_ENTRIES_PER_SECTION

    max_injection = prior_memory.get("max_injection_chars")
    if not isinstance(max_injection, int) or max_injection <= 0:
        max_injection = DEFAULT_MAX_INJECTION_CHARS

    marker = prior_memory.get("deprecation_marker")
    if not isinstance(marker, str) or not marker:
        marker = DEFAULT_DEPRECATION_MARKER

    prior_scopes = prior.get("scopes", {}) if isinstance(prior.get("scopes"), dict) else {}
    prior_agent = prior_scopes.get("agent", {})
    if not isinstance(prior_agent, dict):
        prior_agent = {}
    agent_enabled = prior_agent.get("enabled", True)
    if not isinstance(agent_enabled, bool):
        agent_enabled = True
    agent_inject = prior_agent.get("inject", "none")
    if agent_inject not in ("none", "all"):
        agent_inject = "none"

    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "aimem_version": aimem_version,
        "python_command": python_command,
        "toolchains": {"kiro": kiro, "copilot": copilot},
        "scopes": {
            "project": {"enabled": True, "path": paths.PROJECT_MEMORY},
            "session": {"enabled": True, "path": paths.SESSION_MEMORY},
            "user": {"enabled": user_scope, "path": paths.USER_MEMORY},
            "agent": {
                "enabled": agent_enabled,
                "dir": paths.AGENTS_MEMORY_DIR,
                "inject": agent_inject,
            },
        },
        "index": {"dir": paths.INDEX_DIR},
        "memory": {
            "max_entries_per_section": max_entries,
            "warn_entries_per_section": warn_entries,
            "max_injection_chars": max_injection,
            "deprecation_marker": marker,
            "redaction_patterns": redaction,
        },
    }


def load_existing_config(path: Path) -> dict[str, Any] | None:
    """Load an existing config document if present and valid, else ``None``."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def dumps(config: dict[str, Any]) -> str:
    """Serialize a config document to deterministic JSON text."""
    return json.dumps(config, indent=2, sort_keys=True) + "\n"
