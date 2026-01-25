"""Shared helpers for aimem's project-local hook scripts.

This module is copied verbatim into ``.aimem/hooks/`` and imported by the sibling hook
scripts. It depends only on the Python standard library and never imports the installed
``aimem`` package, so the generated configuration keeps working without aimem installed.

Target runtime: Python 3.8+.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

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
    "index": {"dir": ".aimem/index"},
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

SCOPES = ("project", "user", "session")
MEMORY_SCHEMA_VERSION = 2
LEGACY_MEMORY_SCHEMA_VERSION = 1
MEMORY_RECORD_STATUSES = ("active", "deprecated", "superseded", "invalid")
MEMORY_RECORD_KINDS = (
    "fact",
    "command",
    "convention",
    "decision",
    "gotcha",
    "glossary",
    "note",
    "recommendation",
    "rule",
    "workflow",
    "mistake",
    "structure",
    "diagram",
    "limitation",
    "pattern",
    "external_service",
)
MEMORY_PRIORITIES = ("critical", "high", "medium", "low")
MEMORY_EVIDENCE_LEVELS = (
    "source_code",
    "adr",
    "documentation",
    "user_validated",
    "agent_inferred",
)
MEMORY_VALIDATION_STATUSES = ("verified", "needs_review", "deprecated")
_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_VALIDATION_RANK = {"verified": 0, "needs_review": 1, "deprecated": 2}
_PRIORITY_LABELS = {
    "critical": "🔥 Critical",
    "high": "⭐ High",
    "medium": "Medium",
    "low": "Low",
}
_EVIDENCE_LABELS = {
    "source_code": "✓ Source Code",
    "adr": "✓ ADR",
    "documentation": "✓ Documentation",
    "user_validated": "✓ User Validated",
    "agent_inferred": "Agent Inferred",
}
_RECORD_PREFIX = "aimem:record"
_ID_COMMENT_RE = re.compile(r"<!--\s*aimem:id=([A-Za-z0-9_\-]+)\s*-->")


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
    raw = agent_scope_config(config).get("dir", ".aimem/memory/agents")
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        expanded = os.path.join(project_root(), expanded)
    return os.path.normpath(expanded)


def sanitize_agent(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", (name or "").strip()).strip("-")


def agent_memory_path(config: dict, name: str) -> str:
    stem = sanitize_agent(name)
    return os.path.normpath(os.path.join(agent_dir(config), stem + ".md"))


def list_agent_files(config: dict) -> list:
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
    found = False
    for pattern in compiled:
        if pattern.search(text):
            found = True
            text = pattern.sub("[REDACTED]", text)
    return text, found


def contains_secret(text: str, compiled) -> bool:
    return any(pattern.search(text) for pattern in compiled)


# --- Time and file IO -------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if set(stripped) <= {"-", "*"}:
            continue
        return True
    return False


def normalize_entry_text(text: str) -> str:
    return " ".join(strip_comments(text).split()).strip()


# --- Sidecar index ----------------------------------------------------------------------


def index_dir(config: dict) -> str:
    raw = config.get("index", {}).get("dir", ".aimem/index")
    expanded = os.path.expanduser(raw)
    if not os.path.isabs(expanded):
        expanded = os.path.join(project_root(), expanded)
    return os.path.normpath(expanded)


def index_path(config: dict, scope: str) -> str:
    if scope == "user":
        directory = os.path.join(os.path.expanduser("~"), ".aimem", "index")
        return os.path.join(directory, "user.json")
    stem = sanitize_agent(scope) or scope
    return os.path.join(index_dir(config), stem + ".json")


def _empty_index() -> dict:
    return {"records": [], "schema_version": MEMORY_SCHEMA_VERSION}


def load_index(config: dict, scope: str) -> dict:
    try:
        with open(index_path(config, scope), encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return _empty_index()
    if not isinstance(data, dict):
        return _empty_index()
    records = data.get("records", [])
    if data.get("schema_version") != MEMORY_SCHEMA_VERSION or not isinstance(records, list):
        return _empty_index()
    valid = []
    for record in records:
        if isinstance(record, dict) and validate_record(record)[0]:
            valid.append(record)
    return {"records": valid, "schema_version": MEMORY_SCHEMA_VERSION}


def _record_sort_key(record: dict):
    return (
        str(record.get("scope", "")),
        str(record.get("section", "")),
        _PRIORITY_RANK.get(record.get("priority"), 99),
        _VALIDATION_RANK.get(record.get("validation_status"), 99),
        str(record.get("kind", "")),
        normalize_entry_text(str(record.get("text", ""))).lower(),
        str(record.get("id", "")),
    )


def write_index(config: dict, scope: str, index: dict) -> None:
    records = index.get("records", []) if isinstance(index, dict) else []
    ordered = sorted((item for item in records if isinstance(item, dict)), key=_record_sort_key)
    payload = {"records": ordered, "schema_version": MEMORY_SCHEMA_VERSION}
    atomic_write(index_path(config, scope), json.dumps(payload, indent=2, sort_keys=True) + "\n")


def index_record_map(config: dict, scope: str) -> dict:
    return {record["id"]: record for record in load_index(config, scope).get("records", [])}


def get_index_record(config: dict, scope: str, record_id: str):
    return index_record_map(config, scope).get(record_id)


def upsert_index_record(config: dict, record: dict) -> None:
    ok, reason = validate_record(record)
    if not ok:
        raise ValueError(reason)
    scope = record.get("scope", "project")
    index = load_index(config, scope)
    records = []
    replaced = False
    for existing in index.get("records", []):
        if existing.get("id") == record.get("id"):
            records.append(record)
            replaced = True
        else:
            records.append(existing)
    if not replaced:
        records.append(record)
    write_index(config, scope, {"records": records, "schema_version": MEMORY_SCHEMA_VERSION})


def remove_index_record(config: dict, scope: str, record_id: str) -> None:
    index = load_index(config, scope)
    records = [record for record in index.get("records", []) if record.get("id") != record_id]
    write_index(config, scope, {"records": records, "schema_version": MEMORY_SCHEMA_VERSION})


def set_index_deprecated(config: dict, scope: str, record_id: str, deprecated: bool) -> None:
    index = load_index(config, scope)
    records = []
    changed = False
    for record in index.get("records", []):
        if record.get("id") == record_id:
            record = dict(record)
            record["status"] = "deprecated" if deprecated else "active"
            if deprecated:
                record["validation_status"] = "deprecated"
            elif record.get("validation_status") == "deprecated":
                record["validation_status"] = "needs_review"
            record["updated_at"] = now_iso()
            changed = True
        records.append(record)
    if changed:
        write_index(config, scope, {"records": records, "schema_version": MEMORY_SCHEMA_VERSION})


def prune_index_records(config: dict, scope: str, live_ids: set) -> None:
    index = load_index(config, scope)
    records = [record for record in index.get("records", []) if record.get("id") in live_ids]
    if len(records) != len(index.get("records", [])):
        write_index(config, scope, {"records": records, "schema_version": MEMORY_SCHEMA_VERSION})


# --- Structured memory schema -----------------------------------------------------------


def new_record_id() -> str:
    return "mem_" + uuid.uuid4().hex[:16]


def stable_record_id(scope: str, section: str, kind: str, text: str) -> str:
    value = scope + "\0" + section + "\0" + kind + "\0" + normalize_entry_text(text)
    return "mem_" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def migration_record_id(scope: str, section: str, text: str) -> str:
    value = scope + "\0" + section + "\0" + text
    return "mem_" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def _record_comment(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return "<!-- {0} {1} -->".format(_RECORD_PREFIX, payload)


def _id_comment(record_id: str) -> str:
    return "<!-- aimem:id={0} -->".format(record_id)


def _split_record_comment(body: str):
    marker = "<!-- " + _RECORD_PREFIX + " "
    end = " -->"
    if marker not in body or not body.rstrip().endswith(end):
        return body.rstrip(), None
    start = body.rfind(marker)
    raw = body[start + len(marker) : body.rfind(end)]
    try:
        record = json.loads(raw)
    except ValueError:
        return body.rstrip(), None
    if not isinstance(record, dict):
        return body.rstrip(), None
    return body[:start].rstrip(), record


def _split_id_comment(body: str):
    matches = list(_ID_COMMENT_RE.finditer(body))
    if not matches:
        return body.rstrip(), None
    match = matches[-1]
    visible = (body[: match.start()] + body[match.end() :]).rstrip()
    return visible, match.group(1)


def _split_entry_metadata(body: str):
    visible, record = _split_record_comment(body)
    if isinstance(record, dict):
        return visible, record, record.get("id")
    visible, record_id = _split_id_comment(body)
    return visible, None, record_id


def visible_entry_text(body: str) -> str:
    text, _record, _record_id = _split_entry_metadata(body)
    return text.rstrip()


def record_id_from_entry(body: str):
    _text, record, record_id = _split_entry_metadata(body)
    if isinstance(record, dict):
        return record.get("id")
    return record_id


def _validate_legacy_record(record: dict) -> "tuple[bool, str]":
    required = (
        "schema_version",
        "id",
        "scope",
        "kind",
        "status",
        "source",
        "confidence",
        "validity",
        "relationships",
    )
    for key in required:
        if key not in record:
            return False, "missing '{0}'".format(key)
    if record.get("schema_version") != LEGACY_MEMORY_SCHEMA_VERSION:
        return False, "unsupported schema_version '{0}'".format(record.get("schema_version"))
    if not isinstance(record.get("id"), str) or not record.get("id"):
        return False, "id must be a non-empty string"
    if record.get("scope") not in (*SCOPES, "agent"):
        return False, "scope must be one of project, user, session, agent"
    if record.get("kind") not in MEMORY_RECORD_KINDS:
        return False, "kind must be one of {0}".format(", ".join(MEMORY_RECORD_KINDS))
    if record.get("status") not in MEMORY_RECORD_STATUSES:
        return False, "status must be one of {0}".format(", ".join(MEMORY_RECORD_STATUSES))
    if not isinstance(record.get("source"), str) or not record.get("source"):
        return False, "source must be a non-empty string"
    confidence = record.get("confidence")
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return False, "confidence must be a number from 0 to 1"
    validity = record.get("validity")
    if not isinstance(validity, dict):
        return False, "validity must be an object"
    if not isinstance(validity.get("from"), str) or not validity.get("from"):
        return False, "validity.from must be a non-empty string"
    until = validity.get("until")
    if until is not None and not isinstance(until, str):
        return False, "validity.until must be a string or null"
    if not isinstance(record.get("relationships"), list):
        return False, "relationships must be a list"
    return True, ""


def _validate_string_list(record: dict, key: str, choices=()) -> "tuple[bool, str]":
    value = record.get(key)
    if not isinstance(value, list):
        return False, "{0} must be a list".format(key)
    for item in value:
        if not isinstance(item, str) or not item:
            return False, "{0} must contain non-empty strings".format(key)
        if choices and item not in choices:
            return False, "{0} must contain only {1}".format(key, ", ".join(choices))
    return True, ""


def validate_record(record: dict) -> "tuple[bool, str]":
    version = record.get("schema_version")
    if version == LEGACY_MEMORY_SCHEMA_VERSION:
        return _validate_legacy_record(record)
    required = (
        "schema_version",
        "id",
        "scope",
        "section",
        "kind",
        "status",
        "priority",
        "evidence",
        "validation_status",
        "source",
        "verified_from",
        "confidence",
        "validity",
        "relationships",
        "keywords",
        "text",
        "created_at",
        "updated_at",
    )
    for key in required:
        if key not in record:
            return False, "missing '{0}'".format(key)
    if version != MEMORY_SCHEMA_VERSION:
        return False, "unsupported schema_version '{0}'".format(version)
    if not isinstance(record.get("id"), str) or not record.get("id"):
        return False, "id must be a non-empty string"
    if record.get("scope") not in (*SCOPES, "agent"):
        return False, "scope must be one of project, user, session, agent"
    if not isinstance(record.get("section"), str) or not record.get("section"):
        return False, "section must be a non-empty string"
    if record.get("kind") not in MEMORY_RECORD_KINDS:
        return False, "kind must be one of {0}".format(", ".join(MEMORY_RECORD_KINDS))
    if record.get("status") not in MEMORY_RECORD_STATUSES:
        return False, "status must be one of {0}".format(", ".join(MEMORY_RECORD_STATUSES))
    if record.get("priority") not in MEMORY_PRIORITIES:
        return False, "priority must be one of {0}".format(", ".join(MEMORY_PRIORITIES))
    if record.get("validation_status") not in MEMORY_VALIDATION_STATUSES:
        return False, "validation_status must be one of {0}".format(
            ", ".join(MEMORY_VALIDATION_STATUSES)
        )
    for key, choices in (
        ("evidence", MEMORY_EVIDENCE_LEVELS),
        ("verified_from", ()),
        ("keywords", ()),
    ):
        ok, reason = _validate_string_list(record, key, choices)
        if not ok:
            return False, reason
    if not isinstance(record.get("source"), str) or not record.get("source"):
        return False, "source must be a non-empty string"
    if not isinstance(record.get("text"), str) or not record.get("text"):
        return False, "text must be a non-empty string"
    confidence = record.get("confidence")
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return False, "confidence must be a number from 0 to 1"
    validity = record.get("validity")
    if not isinstance(validity, dict):
        return False, "validity must be an object"
    if not isinstance(validity.get("from"), str) or not validity.get("from"):
        return False, "validity.from must be a non-empty string"
    until = validity.get("until")
    if until is not None and not isinstance(until, str):
        return False, "validity.until must be a string or null"
    if not isinstance(record.get("relationships"), list):
        return False, "relationships must be a list"
    for relation in record.get("relationships"):
        if not isinstance(relation, dict):
            return False, "relationships must contain objects"
        if not isinstance(relation.get("type"), str) or not isinstance(relation.get("id"), str):
            return False, "relationships require string type and id"
    alternatives = record.get("alternatives", [])
    if alternatives is not None and not isinstance(alternatives, list):
        return False, "alternatives must be a list"
    for key in ("created_at", "updated_at"):
        if not isinstance(record.get(key), str) or not record.get(key):
            return False, "{0} must be a non-empty string".format(key)
    return True, ""


def make_record(
    scope: str,
    kind: str,
    status: str,
    source: str,
    confidence: float,
    valid_from: str,
    valid_until,
    relationships: list,
    record_id: str = None,
    section: str = "",
    text: str = "",
    priority: str = "medium",
    evidence=None,
    validation_status: str = "needs_review",
    verified_from=None,
    keywords=None,
    agent: str = "",
    reason: str = "",
    impact: str = "",
    alternatives=None,
) -> dict:
    now = now_iso()
    evidence = list(evidence or ["agent_inferred"])
    verified_from = list(verified_from or [])
    keywords = sorted(set(keywords or []))
    alternatives = list(alternatives or [])
    section = section.strip()
    text = text.strip()
    record = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "id": record_id or stable_record_id(scope, section, kind, text),
        "scope": scope,
        "section": section,
        "kind": kind,
        "status": status,
        "priority": priority,
        "evidence": evidence,
        "validation_status": validation_status,
        "source": source,
        "verified_from": verified_from,
        "confidence": confidence,
        "validity": {"from": valid_from or now, "until": valid_until},
        "relationships": relationships,
        "keywords": keywords,
        "text": text,
        "created_at": now,
        "updated_at": now,
    }
    if agent:
        record["agent"] = sanitize_agent(agent)
    if reason:
        record["reason"] = reason
    if impact:
        record["impact"] = impact
    if alternatives:
        record["alternatives"] = alternatives
    ok, reason = validate_record(record)
    if not ok:
        raise ValueError(reason)
    return record


def legacy_record_to_v2(record: dict, section: str, text: str, source: str = None) -> dict:
    status = record.get("status", "active")
    validation_status = "deprecated" if status == "deprecated" else "needs_review"
    old_source = source or record.get("source") or "migration"
    source_text = str(old_source)
    if source_text == "user":
        evidence = ["user_validated"]
    elif source_text == "migration":
        evidence = ["agent_inferred"]
    else:
        evidence = ["documentation"]
    return make_record(
        str(record.get("scope", "project")),
        str(record.get("kind", "fact")),
        status,
        source_text,
        float(record.get("confidence", 0.5)),
        record.get("validity", {}).get("from") or now_iso(),
        record.get("validity", {}).get("until"),
        list(record.get("relationships", [])),
        record_id=record.get("id") or migration_record_id(
            str(record.get("scope", "project")), section, text
        ),
        section=section,
        text=text,
        priority="medium",
        evidence=evidence,
        validation_status=validation_status,
    )


def attach_record(body: str, record: dict) -> str:
    ok, reason = validate_record(record)
    if not ok:
        raise ValueError(reason)
    text, _old, _old_id = _split_entry_metadata(body)
    return text.rstrip() + "\n  " + _id_comment(record["id"])


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def priority_label(priority: str) -> str:
    return _PRIORITY_LABELS.get(priority, _label(priority))


def evidence_label(evidence: str) -> str:
    return _EVIDENCE_LABELS.get(evidence, _label(evidence))


def format_memory_entry(text: str, record: dict) -> str:
    ok, reason = validate_record(record)
    if not ok:
        raise ValueError(reason)
    lines = [
        "{0} {1}: {2}".format(
            priority_label(record.get("priority", "medium")),
            _label(record.get("kind", "fact")),
            text.strip(),
        )
    ]
    evidence = record.get("evidence", [])
    if evidence:
        lines.append("  Evidence: " + ", ".join(evidence_label(item) for item in evidence))
    lines.append("  Validation: " + _label(record.get("validation_status", "needs_review")))
    lines.append("  Source: " + record.get("source", "manual"))
    verified_from = record.get("verified_from", [])
    if verified_from:
        lines.append("  Verified from: " + ", ".join(verified_from))
    if record.get("reason"):
        lines.append("  Reason: " + record["reason"])
    if record.get("impact"):
        lines.append("  Impact: " + record["impact"])
    alternatives = record.get("alternatives", [])
    if alternatives:
        lines.append("  Alternatives: " + ", ".join(alternatives))
    relationships = record.get("relationships", [])
    if relationships:
        related = ["{0} {1}".format(item.get("type"), item.get("id")) for item in relationships]
        lines.append("  Related: " + ", ".join(related))
    keywords = record.get("keywords", [])
    if keywords:
        lines.append("  Keywords: " + ", ".join(keywords))
    lines.append("  " + _id_comment(record["id"]))
    return "\n".join(lines)


def _entry_blocks(markdown: str) -> list:
    lines = markdown.split("\n")
    blocks = []
    section = ""
    index = 0
    current = None

    def flush(end_index: int) -> None:
        nonlocal current
        if current is None:
            return
        current["end_line"] = end_index - 1
        blocks.append(current)
        current = None

    for line_number, line in enumerate(lines):
        if line.startswith("## "):
            flush(line_number)
            section = line[3:].strip()
            index = 0
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            flush(line_number)
            index += 1
            current = {
                "section": section,
                "index": index,
                "start_line": line_number,
                "end_line": line_number,
                "lines": [line],
            }
            continue
        if current is not None and (not stripped or line.startswith((" ", "\t"))):
            current["lines"].append(line)
            continue
        flush(line_number)
    flush(len(lines))
    return blocks


def _block_body(lines: list) -> str:
    if not lines:
        return ""
    first = lines[0].strip()[2:]
    rest = [line.rstrip() for line in lines[1:]]
    return "\n".join([first] + rest).rstrip()


def parsed_entries(markdown: str, default_scope: str = "", index_records: dict = None) -> list:
    entries = []
    index_records = index_records or {}
    for block in _entry_blocks(markdown):
        body = _block_body(block["lines"])
        visible, legacy_record, record_id = _split_entry_metadata(body)
        record = None
        if record_id and record_id in index_records:
            record = index_records[record_id]
        elif isinstance(legacy_record, dict):
            ok, _reason = validate_record(legacy_record)
            if ok:
                record = legacy_record
        elif record_id:
            record = {"id": record_id, "scope": default_scope}
        deprecated = visible.lstrip().startswith(DEPRECATION_MARKER)
        if isinstance(record, dict):
            if record.get("status") == "deprecated" or record.get("validation_status") == "deprecated":
                deprecated = True
        entries.append(
            {
                "section": block["section"],
                "index": block["index"],
                "deprecated": deprecated,
                "text": visible,
                "record": record,
                "id": record.get("id") if isinstance(record, dict) else record_id,
                "scope": record.get("scope") if isinstance(record, dict) else default_scope,
                "start_line": block["start_line"],
                "end_line": block["end_line"],
                "raw": body,
            }
        )
    return entries


def add_entry(markdown: str, topic: str, entry: str) -> str:
    heading = "## " + topic
    bullet_lines = ("- " + entry).split("\n")
    lines = markdown.splitlines()

    target_id = record_id_from_entry(entry)
    target_text = normalize_entry_text(visible_entry_text(entry)).lower()
    for existing in parsed_entries(markdown):
        if existing["section"] != topic:
            continue
        if target_id and existing.get("id") == target_id:
            return markdown if markdown.endswith("\n") else markdown + "\n"
        existing_text = normalize_entry_text(existing.get("text", "")).lower()
        if existing_text and existing_text == target_text:
            return markdown if markdown.endswith("\n") else markdown + "\n"

    heading_index = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            heading_index = index
            break

    if heading_index is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.extend([heading, *bullet_lines])
        return "\n".join(lines) + "\n"

    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            section_end = index
            break

    insert_at = section_end
    while insert_at - 1 > heading_index and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    for offset, line in enumerate(bullet_lines):
        lines.insert(insert_at + offset, line)
    return "\n".join(lines) + "\n"


# --- Entry addressing and soft-delete ---------------------------------------------------

DEPRECATION_MARKER = "[DEPRECATED]"


def deprecation_marker(config: dict) -> str:
    marker = config.get("memory", {}).get("deprecation_marker", DEPRECATION_MARKER)
    return marker if isinstance(marker, str) and marker else DEPRECATION_MARKER


def is_deprecated_bullet(line: str, marker: str = DEPRECATION_MARKER) -> bool:
    stripped = line.strip()
    if not stripped.startswith("- "):
        return False
    body = stripped[2:]
    visible, record, _record_id = _split_entry_metadata(body)
    if visible.lstrip().startswith(marker):
        return True
    return isinstance(record, dict) and record.get("status") == "deprecated"


def strip_deprecated(markdown: str, marker: str = DEPRECATION_MARKER) -> str:
    lines = markdown.split("\n")
    remove = set()
    for entry in parsed_entries(markdown):
        if not entry["deprecated"]:
            continue
        for index in range(entry["start_line"], entry["end_line"] + 1):
            remove.add(index)
    kept = [line for index, line in enumerate(lines) if index not in remove]
    return "\n".join(kept)


def list_entries(markdown: str) -> list:
    return [
        (entry["section"], entry["index"], entry["deprecated"], entry["text"])
        for entry in parsed_entries(markdown)
    ]


def _locate_bullet_range(lines: list, section: str, index: int):
    text = "\n".join(lines)
    for entry in parsed_entries(text):
        if entry["section"] == section and entry["index"] == index:
            return entry["start_line"], entry["end_line"]
    return None


def _locate_bullet(lines: list, section: str, index: int):
    located = _locate_bullet_range(lines, section, index)
    return located[0] if located else None


def delete_entry(markdown: str, section: str, index: int):
    lines = markdown.split("\n")
    located = _locate_bullet_range(lines, section, index)
    if located is None:
        return markdown, False
    start, end = located
    del lines[start : end + 1]
    text = "\n".join(lines)
    return (text if text.endswith("\n") else text + "\n"), True


def set_deprecated(
    markdown: str, section: str, index: int, deprecated: bool, marker: str = DEPRECATION_MARKER
):
    lines = markdown.split("\n")
    i = _locate_bullet(lines, section, index)
    if i is None:
        return markdown, False
    line = lines[i]
    indent = line[: len(line) - len(line.lstrip())]
    body = line.strip()[2:]
    visible, record = _split_record_comment(body)
    already = visible.lstrip().startswith(marker)
    clean_visible = visible.lstrip()[len(marker) :].lstrip() if already else visible
    body = marker + " " + clean_visible.lstrip() if deprecated else clean_visible
    if isinstance(record, dict):
        record["status"] = "deprecated" if deprecated else "active"
        record["updated_at"] = now_iso()
        body = body + " " + _record_comment(record)
    lines[i] = indent + "- " + body
    text = "\n".join(lines)
    return (text if text.endswith("\n") else text + "\n"), True


def count_active_entries(markdown: str, section: str) -> int:
    return sum(
        1 for sec, _idx, deprecated, _text in list_entries(markdown) if sec == section and not deprecated
    )


def consolidate(markdown: str, max_entries: int, compiled, marker: str = DEPRECATION_MARKER) -> str:
    redacted, _ = redact(markdown, compiled)
    lines = redacted.split("\n")
    remove = set()
    seen = {}
    counts = {}
    for entry in parsed_entries(redacted):
        section = entry["section"]
        key = normalize_entry_text(entry["text"]).lower()
        seen.setdefault(section, set())
        counts.setdefault(section, 0)
        should_remove = False
        if key in seen[section]:
            should_remove = True
        else:
            seen[section].add(key)
        if not entry["deprecated"]:
            if counts[section] >= max_entries:
                should_remove = True
            else:
                counts[section] += 1
        if should_remove and not entry["deprecated"]:
            for index in range(entry["start_line"], entry["end_line"] + 1):
                remove.add(index)
    result = [line for index, line in enumerate(lines) if index not in remove]
    text = collapse_blank_lines("\n".join(result))
    if not text.endswith("\n"):
        text += "\n"
    return text
