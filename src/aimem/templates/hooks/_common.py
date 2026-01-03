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
        "agent": {"enabled": True, "dir": ".aimem/memory/agents", "inject": "none"},
    },
    "memory": {
        "max_entries_per_section": 200,
        "warn_entries_per_section": 50,
        "max_injection_chars": 12000,
        "deprecation_marker": "[DEPRECATED]",
        "redaction_patterns": [
            r"(?i)\b(api[_-]?key|secret|password|passwd|token|client[_-]?secret)\b\s*[:=]\s*\S+",
            r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}",
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
        ],
    },
}

# Canonical single-file scopes. Agent-scoped memory is a separate, directory-backed
# dimension resolved through the ``agent_*`` helpers below.
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
    if scope == "agent":
        return bool(agent_scope_config(config).get("enabled", True))
    return bool(scope_config(config, scope).get("enabled", False))


# --- Agent-scoped memory ----------------------------------------------------------------


def agent_scope_config(config: dict) -> dict:
    value = config.get("scopes", {}).get("agent", {})
    return value if isinstance(value, dict) else {}


def agent_dir(config: dict) -> str:
    """Return the absolute directory that holds per-agent memory files."""
    raw = agent_scope_config(config).get("dir", ".aimem/memory/agents")
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        expanded = os.path.join(project_root(), expanded)
    return os.path.normpath(expanded)


def sanitize_agent(name: str) -> str:
    """Reduce an agent name to a safe file stem (prevents path traversal)."""
    return re.sub(r"[^A-Za-z0-9_-]+", "-", (name or "").strip()).strip("-")


def agent_memory_path(config: dict, name: str) -> str:
    """Return the absolute path to a single agent's memory file."""
    stem = sanitize_agent(name)
    return os.path.normpath(os.path.join(agent_dir(config), stem + ".md"))


def list_agent_files(config: dict) -> list:
    """Return ``(agent_name, path)`` for each agent memory file, excluding README."""
    directory = agent_dir(config)
    results = []
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return results
    for entry in names:
        if not entry.endswith(".md") or entry.lower() == "readme.md":
            continue
        results.append((entry[:-3], os.path.join(directory, entry)))
    return results


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


# --- Entry addressing and soft-delete (deprecation) -------------------------------------

DEPRECATION_MARKER = "[DEPRECATED]"


def deprecation_marker(config: dict) -> str:
    marker = config.get("memory", {}).get("deprecation_marker", DEPRECATION_MARKER)
    return marker if isinstance(marker, str) and marker else DEPRECATION_MARKER


def is_deprecated_bullet(line: str, marker: str = DEPRECATION_MARKER) -> bool:
    stripped = line.strip()
    if not stripped.startswith("- "):
        return False
    return stripped[2:].lstrip().startswith(marker)


def strip_deprecated(markdown: str, marker: str = DEPRECATION_MARKER) -> str:
    """Drop deprecated bullets so they stay on disk but are not injected into context."""
    kept = [line for line in markdown.split("\n") if not is_deprecated_bullet(line, marker)]
    return "\n".join(kept)


def list_entries(markdown: str) -> list:
    """Return ``(section, index, deprecated, text)`` per bullet, 1-based within each section."""
    entries = []
    section = ""
    index = 0
    for line in markdown.split("\n"):
        if line.startswith("## "):
            section = line[3:].strip()
            index = 0
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            index += 1
            entries.append((section, index, is_deprecated_bullet(line), stripped[2:]))
    return entries


def _locate_bullet(lines: list, section: str, index: int):
    current = ""
    count = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            current = line[3:].strip()
            count = 0
            continue
        if current == section and line.strip().startswith("- "):
            count += 1
            if count == index:
                return i
    return None


def delete_entry(markdown: str, section: str, index: int):
    """Hard-remove the ``index``-th bullet under ``section``. Returns ``(text, removed)``."""
    lines = markdown.split("\n")
    i = _locate_bullet(lines, section, index)
    if i is None:
        return markdown, False
    del lines[i]
    text = "\n".join(lines)
    return (text if text.endswith("\n") else text + "\n"), True


def set_deprecated(
    markdown: str, section: str, index: int, deprecated: bool, marker: str = DEPRECATION_MARKER
):
    """Toggle the deprecation marker on a bullet. Returns ``(text, changed)``."""
    lines = markdown.split("\n")
    i = _locate_bullet(lines, section, index)
    if i is None:
        return markdown, False
    line = lines[i]
    indent = line[: len(line) - len(line.lstrip())]
    body = line.strip()[2:]
    already = body.lstrip().startswith(marker)
    if deprecated and not already:
        body = marker + " " + body.lstrip()
    elif not deprecated and already:
        body = body.lstrip()[len(marker) :].lstrip()
    lines[i] = indent + "- " + body
    text = "\n".join(lines)
    return (text if text.endswith("\n") else text + "\n"), True


def count_active_entries(markdown: str, section: str) -> int:
    """Count non-deprecated bullets under ``section``."""
    return sum(
        1 for sec, _idx, deprecated, _text in list_entries(markdown) if sec == section and not deprecated
    )


def consolidate(markdown: str, max_entries: int, compiled, marker: str = DEPRECATION_MARKER) -> str:
    """De-duplicate bullets per section, cap active entries, redact secrets, tidy blanks.

    Deprecated (soft-deleted) bullets are always preserved and never count toward the
    active-entry cap.
    """
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
            if key in seen:
                continue
            seen.add(key)
            if not is_deprecated_bullet(line, marker):
                if count >= max_entries:
                    continue
                count += 1
        result.append(line)
    text = collapse_blank_lines("\n".join(result))
    if not text.endswith("\n"):
        text += "\n"
    return text
