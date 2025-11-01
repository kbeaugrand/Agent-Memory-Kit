"""Shared helpers for aimem's project-local hook scripts.

This module is copied verbatim into ``.aimem/hooks/`` and imported by the sibling hook
scripts. It depends only on the Python standard library and never imports the installed
``aimem`` package, so the generated configuration keeps working without aimem installed.

Target runtime: Python 3.8+.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

# --- Location helpers -------------------------------------------------------------------


def hooks_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def aimem_dir() -> str:
    return os.path.dirname(hooks_dir())


def project_root() -> str:
    return os.path.dirname(aimem_dir())


# --- Configuration ----------------------------------------------------------------------

_DEFAULT_CONFIG = {
    "python_command": "python3",
    "scopes": {
        "project": {"enabled": True, "path": ".aimem/memory/project.md"},
        "session": {"enabled": True, "path": ".aimem/memory/session/current.md"},
        "user": {"enabled": False, "path": "~/.aimem/memory/user.md"},
    },
    "memory": {
        "max_entries_per_section": 200,
        "redaction_patterns": [
            r"(?i)\b(api[_-]?key|secret|password|passwd|token|client[_-]?secret)\b\s*[:=]\s*\S+",
            r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}",
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        ],
    },
}

SCOPES = ("project", "user", "session")


def load_config() -> dict:
    """Load ``.aimem/config.json``, falling back to built-in defaults on any error."""
    path = os.path.join(aimem_dir(), "config.json")
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        data = {}
    return _merge(_DEFAULT_CONFIG, data if isinstance(data, dict) else {})


def _merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def scope_config(config: dict, scope: str) -> dict:
    scopes = config.get("scopes", {})
    value = scopes.get(scope, {})
    return value if isinstance(value, dict) else {}


def scope_path(config: dict, scope: str) -> str:
    """Return the absolute filesystem path for a memory scope."""
    raw = scope_config(config, scope).get("path", "")
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        expanded = os.path.join(project_root(), expanded)
    return os.path.normpath(expanded)


def scope_enabled(config: dict, scope: str) -> bool:
    return bool(scope_config(config, scope).get("enabled", False))


# --- Redaction --------------------------------------------------------------------------


def compile_redactions(config: dict):
    patterns = config.get("memory", {}).get("redaction_patterns", [])
    compiled = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error:
            continue
    return compiled


def redact(text: str, compiled) -> "tuple[str, bool]":
    """Replace any matched secrets with ``[REDACTED]``. Returns ``(text, found)``."""
    found = False
    for pattern in compiled:
        if pattern.search(text):
            found = True
            text = pattern.sub("[REDACTED]", text)
    return text, found


def contains_secret(text: str, compiled) -> bool:
    return any(pattern.search(text) for pattern in compiled)


# --- Time -------------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- File IO ----------------------------------------------------------------------------


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def atomic_write(path: str, text: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp = path + ".aimem-tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp, path)


# --- Markdown helpers -------------------------------------------------------------------

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_BLANK_RUN_RE = re.compile(r"\n{3,}")


def strip_comments(markdown: str) -> str:
    return _COMMENT_RE.sub("", markdown)


def collapse_blank_lines(text: str) -> str:
    return _BLANK_RUN_RE.sub("\n\n", text)


def has_content(markdown: str) -> bool:
    """True if the markdown has any substantive line (not blank, not a heading)."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if set(stripped) <= {"-", "*"}:
            continue
        return True
    return False


def add_entry(markdown: str, topic: str, entry: str) -> str:
    """Append ``- entry`` under the ``## topic`` heading, creating it if needed.

    Exact-duplicate bullets in the target section are not added again.
    """
    heading = "## " + topic
    bullet = "- " + entry
    lines = markdown.splitlines()

    heading_index = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            heading_index = index
            break

    if heading_index is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.extend([heading, "", bullet])
        return "\n".join(lines) + "\n"

    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            section_end = index
            break

    for line in lines[heading_index + 1 : section_end]:
        if line.strip() == bullet:
            return markdown if markdown.endswith("\n") else markdown + "\n"

    insert_at = section_end
    while insert_at - 1 > heading_index and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, bullet)
    return "\n".join(lines) + "\n"


def consolidate(markdown: str, max_entries: int, compiled) -> str:
    """De-duplicate bullets per section, cap section size, redact secrets, tidy blanks."""
    redacted, _ = redact(markdown, compiled)
    result = []
    seen = set()
    count = 0
    for line in redacted.split("\n"):
        if line.startswith("## "):
            seen = set()
            count = 0
            result.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            key = " ".join(stripped.split())
            if key in seen or count >= max_entries:
                continue
            seen.add(key)
            count += 1
        result.append(line)
    text = collapse_blank_lines("\n".join(result))
    if not text.endswith("\n"):
        text += "\n"
    return text
