"""Provider-neutral memory operations used by the aimem MCP server."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aimem.core import config as config_mod
from aimem.core import paths
from aimem.core.vector_db import LocalVectorDatabase

SCOPES = ("project", "user", "session")
ALL_SCOPES = (*SCOPES, "agent")
MEMORY_SCHEMA_VERSION = 2
PROPOSAL_SCHEMA_VERSION = 1
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
CONFLICT_RELATIONSHIPS = {"contradicts", "supersedes", "superseded_by"}

_PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_VALIDATION_RANK = {"verified": 0, "needs_review": 1, "deprecated": 2}
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_ID_COMMENT_RE = re.compile(r"<!--\s*aimem:id=([A-Za-z0-9_\-]+)\s*-->")


class MemoryStoreError(RuntimeError):
    """Raised for expected memory service errors with stable error codes."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class MemoryEntry:
    """A parsed memory entry plus its address and metadata."""

    id: str | None
    scope: str
    target: str
    path: Path
    section: str
    index: int
    text: str
    record: dict[str, Any] | None
    deprecated: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scope": self.scope,
            "target": self.target,
            "path": self.path.as_posix(),
            "section": self.section,
            "index": self.index,
            "text": self.text,
            "record": self.record,
            "deprecated": self.deprecated,
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def strip_comments(markdown: str) -> str:
    return _COMMENT_RE.sub("", markdown)


def normalize_entry_text(text: str) -> str:
    return " ".join(strip_comments(text).split()).strip()


def stable_record_id(scope: str, section: str, kind: str, text: str) -> str:
    value = scope + "\0" + section + "\0" + kind + "\0" + normalize_entry_text(text)
    return "mem_" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def sanitize_agent(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", (name or "").strip()).strip("-")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".aimem-tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _id_comment(record_id: str) -> str:
    return f"<!-- aimem:id={record_id} -->"


def _split_id_comment(body: str) -> tuple[str, str | None]:
    matches = list(_ID_COMMENT_RE.finditer(body))
    if not matches:
        return body.rstrip(), None
    match = matches[-1]
    visible = (body[: match.start()] + body[match.end() :]).rstrip()
    return visible, match.group(1)


def _entry_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = markdown.split("\n")
    blocks: list[dict[str, Any]] = []
    section = ""
    index = 0
    current: dict[str, Any] | None = None

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


def _block_body(lines: list[str]) -> str:
    if not lines:
        return ""
    first = lines[0].strip()[2:]
    rest = [line.rstrip() for line in lines[1:]]
    return "\n".join([first, *rest]).rstrip()


def _label(value: str) -> str:
    return value.replace("_", " ").title()


def _format_memory_entry(text: str, record: dict[str, Any]) -> str:
    lines = [f"{_label(record['priority'])} {_label(record['kind'])}: {text.strip()}"]
    evidence = record.get("evidence", [])
    if evidence:
        lines.append("  Evidence: " + ", ".join(_label(item) for item in evidence))
    lines.append("  Validation: " + _label(str(record.get("validation_status", "needs_review"))))
    lines.append("  Source: " + str(record.get("source", "manual")))
    verified_from = record.get("verified_from", [])
    if verified_from:
        lines.append("  Verified from: " + ", ".join(str(item) for item in verified_from))
    relationships = record.get("relationships", [])
    if relationships:
        related = [f"{item.get('type')} {item.get('id')}" for item in relationships]
        lines.append("  Related: " + ", ".join(related))
    keywords = record.get("keywords", [])
    if keywords:
        lines.append("  Keywords: " + ", ".join(str(item) for item in keywords))
    lines.append("  " + _id_comment(str(record["id"])))
    return "\n".join(lines)


def _record_id_from_entry(body: str) -> str | None:
    _visible, record_id = _split_id_comment(body)
    return record_id


def _add_entry(markdown: str, topic: str, entry: str) -> str:
    heading = "## " + topic
    bullet_lines = ("- " + entry).split("\n")
    lines = markdown.splitlines()
    target_id = _record_id_from_entry(entry)
    target_text = normalize_entry_text(_split_id_comment(entry)[0]).lower()

    for existing in _parsed_entries(markdown, "", {}):
        if existing["section"] != topic:
            continue
        if target_id and existing.get("id") == target_id:
            return markdown if markdown.endswith("\n") else markdown + "\n"
        existing_text = normalize_entry_text(str(existing.get("text", ""))).lower()
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


def _parsed_entries(
    markdown: str, default_scope: str, index_records: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for block in _entry_blocks(markdown):
        body = _block_body(block["lines"])
        visible, record_id = _split_id_comment(body)
        record = index_records.get(record_id or "")
        deprecated = visible.lstrip().startswith("[DEPRECATED]")
        if record and (
            record.get("status") == "deprecated" or record.get("validation_status") == "deprecated"
        ):
            deprecated = True
        entries.append(
            {
                "section": block["section"],
                "index": block["index"],
                "deprecated": deprecated,
                "text": visible,
                "record": record
                if record
                else ({"id": record_id, "scope": default_scope} if record_id else None),
                "id": record.get("id") if record else record_id,
            }
        )
    return entries


def _validate_string_list(record: dict[str, Any], key: str, choices: tuple[str, ...] = ()) -> None:
    value = record.get(key)
    if not isinstance(value, list):
        raise MemoryStoreError("INVALID_RECORD", f"{key} must be a list")
    for item in value:
        if not isinstance(item, str) or not item:
            raise MemoryStoreError("INVALID_RECORD", f"{key} must contain non-empty strings")
        if choices and item not in choices:
            raise MemoryStoreError("INVALID_RECORD", f"{key} contains unsupported value")


def validate_record(record: dict[str, Any]) -> None:
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
            raise MemoryStoreError("INVALID_RECORD", f"missing '{key}'")
    if record.get("schema_version") != MEMORY_SCHEMA_VERSION:
        raise MemoryStoreError("INVALID_RECORD", "unsupported schema_version")
    if record.get("scope") not in ALL_SCOPES:
        raise MemoryStoreError("INVALID_RECORD", "unsupported scope")
    if record.get("kind") not in MEMORY_RECORD_KINDS:
        raise MemoryStoreError("INVALID_RECORD", "unsupported kind")
    if record.get("status") not in MEMORY_RECORD_STATUSES:
        raise MemoryStoreError("INVALID_RECORD", "unsupported status")
    if record.get("priority") not in MEMORY_PRIORITIES:
        raise MemoryStoreError("INVALID_RECORD", "unsupported priority")
    if record.get("validation_status") not in MEMORY_VALIDATION_STATUSES:
        raise MemoryStoreError("INVALID_RECORD", "unsupported validation_status")
    _validate_string_list(record, "evidence", MEMORY_EVIDENCE_LEVELS)
    _validate_string_list(record, "verified_from")
    _validate_string_list(record, "keywords")
    if not isinstance(record.get("id"), str) or not record["id"]:
        raise MemoryStoreError("INVALID_RECORD", "id must be a non-empty string")
    if not isinstance(record.get("section"), str) or not record["section"]:
        raise MemoryStoreError("INVALID_RECORD", "section must be a non-empty string")
    if not isinstance(record.get("text"), str) or not record["text"]:
        raise MemoryStoreError("INVALID_RECORD", "text must be a non-empty string")
    confidence = record.get("confidence")
    if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
        raise MemoryStoreError("INVALID_RECORD", "confidence must be from 0 to 1")
    validity = record.get("validity")
    if not isinstance(validity, dict) or not isinstance(validity.get("from"), str):
        raise MemoryStoreError("INVALID_RECORD", "validity.from is required")
    relationships = record.get("relationships")
    if not isinstance(relationships, list):
        raise MemoryStoreError("INVALID_RECORD", "relationships must be a list")
    for relation in relationships:
        if not isinstance(relation, dict):
            raise MemoryStoreError("INVALID_RECORD", "relationships must contain objects")
        if not isinstance(relation.get("type"), str) or not isinstance(relation.get("id"), str):
            raise MemoryStoreError("INVALID_RECORD", "relationships require type and id")


def make_record(
    *,
    scope: str,
    section: str,
    text: str,
    kind: str = "fact",
    status: str = "active",
    priority: str = "medium",
    evidence: list[str] | None = None,
    validation_status: str = "needs_review",
    source: str = "manual",
    verified_from: list[str] | None = None,
    confidence: float = 0.8,
    relationships: list[dict[str, str]] | None = None,
    keywords: list[str] | None = None,
    agent: str = "",
    record_id: str | None = None,
) -> dict[str, Any]:
    now = now_iso()
    clean_text = text.strip()
    clean_section = section.strip()
    record: dict[str, Any] = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "id": record_id or stable_record_id(scope, clean_section, kind, clean_text),
        "scope": scope,
        "section": clean_section,
        "kind": kind,
        "status": status,
        "priority": priority,
        "evidence": list(evidence or ["agent_inferred"]),
        "validation_status": validation_status,
        "source": source.strip() or "manual",
        "verified_from": list(verified_from or []),
        "confidence": confidence,
        "validity": {"from": now, "until": None},
        "relationships": list(relationships or []),
        "keywords": sorted(set(keywords or [])),
        "text": clean_text,
        "created_at": now,
        "updated_at": now,
    }
    if agent:
        record["agent"] = sanitize_agent(agent)
    validate_record(record)
    return record


class MemoryStore:
    """File-backed memory store for an initialized aimem project."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        config = config_mod.load_existing_config(self.root / paths.CONFIG_FILE)
        if config is None:
            raise MemoryStoreError(
                "CONFIG_NOT_FOUND", f"No aimem config found at {self.root / paths.CONFIG_FILE}"
            )
        self.config = config
        self.vector_db = LocalVectorDatabase(self.vector_index_path())
        self._vector_loaded = False

    @classmethod
    def from_directory(cls, directory: str | os.PathLike[str] | None = None) -> MemoryStore:
        return cls(resolve_project_root(directory))

    def scope_enabled(self, scope: str) -> bool:
        if scope == "agent":
            scope_config = self.config.get("scopes", {}).get("agent", {})
            if isinstance(scope_config, dict):
                return bool(scope_config.get("enabled", True))
            return True
        scope_config = self.config.get("scopes", {}).get(scope, {})
        if isinstance(scope_config, dict):
            return bool(scope_config.get("enabled", False))
        return False

    def scope_path(self, scope: str) -> Path:
        scope_config = self.config.get("scopes", {}).get(scope, {})
        raw = scope_config.get("path", "") if isinstance(scope_config, dict) else ""
        if not isinstance(raw, str) or not raw:
            raise MemoryStoreError("SCOPE_NOT_FOUND", f"No path configured for scope '{scope}'")
        expanded = Path(os.path.expanduser(raw))
        return expanded if expanded.is_absolute() else self.root / expanded

    def agent_dir(self) -> Path:
        scope_config = self.config.get("scopes", {}).get("agent", {})
        raw = (
            scope_config.get("dir", paths.AGENTS_MEMORY_DIR)
            if isinstance(scope_config, dict)
            else paths.AGENTS_MEMORY_DIR
        )
        expanded = Path(os.path.expanduser(str(raw)))
        return expanded if expanded.is_absolute() else self.root / expanded

    def agent_path(self, agent: str) -> Path:
        clean = sanitize_agent(agent)
        if not clean:
            raise MemoryStoreError("AGENT_REQUIRED", "Agent scope requires a non-empty agent name")
        return self.agent_dir() / f"{clean}.md"

    def proposal_dir(self) -> Path:
        mcp_config = self.config.get("mcp", {})
        raw = (
            mcp_config.get("proposal_dir", paths.PROPOSALS_DIR)
            if isinstance(mcp_config, dict)
            else paths.PROPOSALS_DIR
        )
        expanded = Path(os.path.expanduser(str(raw)))
        return expanded if expanded.is_absolute() else self.root / expanded

    def _index_dir(self) -> Path:
        index_config = self.config.get("index", {})
        raw = (
            index_config.get("dir", paths.INDEX_DIR)
            if isinstance(index_config, dict)
            else paths.INDEX_DIR
        )
        expanded = Path(os.path.expanduser(str(raw)))
        return expanded if expanded.is_absolute() else self.root / expanded

    def vector_index_path(self) -> Path:
        index_config = self.config.get("index", {})
        raw = (
            index_config.get("vector_path", paths.VECTOR_INDEX)
            if isinstance(index_config, dict)
            else paths.VECTOR_INDEX
        )
        expanded = Path(os.path.expanduser(str(raw)))
        return expanded if expanded.is_absolute() else self.root / expanded

    def _index_path(self, scope: str) -> Path:
        if scope == "user":
            return Path(os.path.expanduser("~")) / ".aimem" / "index" / "user.json"
        return self._index_dir() / f"{sanitize_agent(scope) or scope}.json"

    def _load_index(self, scope: str) -> dict[str, dict[str, Any]]:
        path = self._index_path(scope)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict) or data.get("schema_version") != MEMORY_SCHEMA_VERSION:
            return {}
        records = data.get("records", [])
        if not isinstance(records, list):
            return {}
        valid: dict[str, dict[str, Any]] = {}
        for record in records:
            if isinstance(record, dict):
                try:
                    validate_record(record)
                except MemoryStoreError:
                    continue
                valid[str(record["id"])] = record
        return valid

    def _write_index(self, scope: str, records: list[dict[str, Any]]) -> None:
        def sort_key(record: dict[str, Any]) -> tuple[object, ...]:
            return (
                str(record.get("scope", "")),
                str(record.get("section", "")),
                _PRIORITY_RANK.get(str(record.get("priority", "")), 99),
                _VALIDATION_RANK.get(str(record.get("validation_status", "")), 99),
                str(record.get("kind", "")),
                normalize_entry_text(str(record.get("text", ""))).lower(),
                str(record.get("id", "")),
            )

        payload = {
            "records": sorted(records, key=sort_key),
            "schema_version": MEMORY_SCHEMA_VERSION,
        }
        _atomic_write(self._index_path(scope), json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _upsert_record(self, record: dict[str, Any]) -> None:
        validate_record(record)
        scope = str(record["scope"])
        records = list(self._load_index(scope).values())
        replaced = False
        updated: list[dict[str, Any]] = []
        for existing in records:
            if existing.get("id") == record.get("id"):
                updated.append(record)
                replaced = True
            else:
                updated.append(existing)
        if not replaced:
            updated.append(record)
        self._write_index(scope, updated)

    def _target_path(self, scope: str, agent: str = "") -> tuple[str, Path]:
        if scope not in ALL_SCOPES:
            raise MemoryStoreError("INVALID_SCOPE", f"Unsupported scope '{scope}'")
        if not self.scope_enabled(scope):
            raise MemoryStoreError("SCOPE_DISABLED", f"Scope '{scope}' is disabled")
        if scope == "agent":
            clean = sanitize_agent(agent)
            return f"agent:{clean}", self.agent_path(clean)
        return scope, self.scope_path(scope)

    def _iter_targets(
        self, scope: str | None = None, agent: str | None = None
    ) -> list[tuple[str, str, Path]]:
        targets: list[tuple[str, str, Path]] = []
        if scope:
            if scope == "agent" and not agent:
                for path in sorted(self.agent_dir().glob("*.md")):
                    if path.name.lower() != "readme.md":
                        targets.append(("agent", f"agent:{path.stem}", path))
                return targets
            target, path = self._target_path(scope, agent or "")
            return [(scope, target, path)]
        for canonical in SCOPES:
            if self.scope_enabled(canonical):
                targets.append((canonical, canonical, self.scope_path(canonical)))
        if self.scope_enabled("agent"):
            for path in sorted(self.agent_dir().glob("*.md")):
                if path.name.lower() != "readme.md":
                    targets.append(("agent", f"agent:{path.stem}", path))
        return targets

    def entries(
        self,
        *,
        scope: str | None = None,
        agent: str | None = None,
        include_deprecated: bool = False,
    ) -> list[MemoryEntry]:
        results: list[MemoryEntry] = []
        for entry_scope, target, path in self._iter_targets(scope, agent):
            records = self._load_index(entry_scope)
            for item in _parsed_entries(_read_text(path), entry_scope, records):
                if item["deprecated"] and not include_deprecated:
                    continue
                record = item["record"] if isinstance(item["record"], dict) else None
                results.append(
                    MemoryEntry(
                        id=item.get("id"),
                        scope=str(record.get("scope", entry_scope)) if record else entry_scope,
                        target=target,
                        path=path,
                        section=str(item["section"]),
                        index=int(item["index"]),
                        text=str(item["text"]),
                        record=record,
                        deprecated=bool(item["deprecated"]),
                    )
                )
        return results

    def get(self, record_id: str, *, include_deprecated: bool = True) -> dict[str, Any]:
        for entry in self.entries(include_deprecated=include_deprecated):
            if entry.id == record_id:
                return entry.to_dict()
        raise MemoryStoreError("NOT_FOUND", f"No memory entry found for id '{record_id}'")

    def load_vector_database(self) -> dict[str, Any]:
        """Load all current memory entries into the local vector database."""
        documents: list[tuple[str, str, dict[str, Any]]] = []
        for entry in self.entries(include_deprecated=True):
            document_id = entry.id or f"{entry.target}:{entry.section}:{entry.index}"
            record = entry.record or {}
            text = " ".join(
                [
                    entry.scope,
                    entry.section,
                    str(record.get("kind", "")),
                    str(record.get("priority", "")),
                    str(record.get("validation_status", "")),
                    str(record.get("text", "")),
                    entry.text,
                    " ".join(str(item) for item in record.get("keywords", [])),
                ]
            )
            documents.append(
                (
                    document_id,
                    text,
                    {
                        "deprecated": entry.deprecated,
                        "index": entry.index,
                        "path": entry.path.as_posix(),
                        "scope": entry.scope,
                        "section": entry.section,
                        "target": entry.target,
                    },
                )
            )
        self.vector_db.replace(documents)
        self._vector_loaded = True
        return {"documents": len(documents), "path": self.vector_index_path().as_posix()}

    def search(
        self,
        *,
        query: str = "",
        scope: str | None = None,
        agent: str | None = None,
        include_deprecated: bool = False,
        kind: str | None = None,
        priority: str | None = None,
        validation_status: str | None = None,
        keyword: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        if not self._vector_loaded:
            self.load_vector_database()
        default_limit = self.config.get("mcp", {}).get("default_search_limit", 20)
        max_results = limit if isinstance(limit, int) and limit > 0 else int(default_limit)
        terms = [term.lower() for term in query.split() if term.strip()]
        keyword_lower = keyword.lower() if keyword else None
        vector_query = " ".join(part for part in (query, keyword or "") if part)
        vector_matches = {
            str(item["id"]): float(item["similarity"])
            for item in self.vector_db.search(vector_query, limit=None)
        }
        rows: list[tuple[tuple[float, int, int, int, str, int], dict[str, Any]]] = []
        for entry in self.entries(scope=scope, agent=agent, include_deprecated=include_deprecated):
            record = entry.record or {}
            entry_id = entry.id or f"{entry.target}:{entry.section}:{entry.index}"
            if kind and record.get("kind") != kind:
                continue
            if priority and record.get("priority") != priority:
                continue
            if validation_status and record.get("validation_status") != validation_status:
                continue
            haystack = " ".join(
                [
                    entry.section,
                    entry.text,
                    str(record.get("text", "")),
                    " ".join(str(item) for item in record.get("keywords", [])),
                ]
            ).lower()
            similarity = vector_matches.get(entry_id, 0.0)
            lexical_match = any(term in haystack for term in terms)
            if vector_query and similarity <= 0 and not lexical_match:
                continue
            if keyword_lower and keyword_lower not in haystack:
                continue
            match_score = sum(
                3 if term in str(record.get("text", "")).lower() else 1 for term in terms
            )
            priority_rank = _PRIORITY_RANK.get(str(record.get("priority", "medium")), 99)
            validation_rank = _VALIDATION_RANK.get(
                str(record.get("validation_status", "needs_review")), 99
            )
            row = entry.to_dict()
            row["match"] = {
                "query": query,
                "score": match_score,
                "similarity": similarity,
                "vector_database": self.vector_index_path().as_posix(),
            }
            sort_key = (
                -similarity,
                -match_score,
                priority_rank,
                validation_rank,
                entry.scope,
                entry.index,
            )
            rows.append((sort_key, row))
        rows.sort(key=lambda item: item[0])
        return {"entries": [row for _key, row in rows[:max_results]], "total": len(rows)}

    def _compile_redactions(self) -> list[re.Pattern[str]]:
        patterns = self.config.get("memory", {}).get("redaction_patterns", [])
        compiled: list[re.Pattern[str]] = []
        if not isinstance(patterns, list):
            return compiled
        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            try:
                compiled.append(re.compile(pattern))
            except re.error:
                continue
        return compiled

    def _redact(self, text: str) -> tuple[str, bool]:
        redacted = text
        found = False
        for pattern in self._compile_redactions():
            if pattern.search(redacted):
                found = True
                redacted = pattern.sub("[REDACTED]", redacted)
        return redacted, found

    def record(self, record: dict[str, Any]) -> dict[str, Any]:
        validate_record(record)
        scope = str(record["scope"])
        target, path = self._target_path(scope, str(record.get("agent", "")))
        title = (
            "Agent Memory: " + target.split(":", 1)[1]
            if scope == "agent"
            else f"{_label(scope)} Memory"
        )
        existing = _read_text(path)
        if not existing.strip():
            existing = f"# {title}\n\n"
        entry = _format_memory_entry(str(record["text"]), record)
        updated = _add_entry(existing, str(record["section"]), entry)
        _atomic_write(path, updated)
        self._upsert_record(record)
        self.load_vector_database()
        return self.get(str(record["id"]))

    def propose(
        self,
        *,
        scope: str,
        topic: str,
        text: str,
        kind: str = "fact",
        priority: str = "medium",
        evidence: list[str] | None = None,
        validation_status: str = "needs_review",
        source: str = "mcp",
        verified_from: list[str] | None = None,
        confidence: float = 0.8,
        relationships: list[dict[str, str]] | None = None,
        keywords: list[str] | None = None,
        agent: str = "",
    ) -> dict[str, Any]:
        clean_text, redacted = self._redact(text.strip())
        if not clean_text:
            raise MemoryStoreError("INVALID_PROPOSAL", "Proposed memory text is empty")
        record = make_record(
            scope=scope,
            section=topic,
            text=clean_text,
            kind=kind,
            priority=priority,
            evidence=evidence,
            validation_status=validation_status,
            source=source,
            verified_from=verified_from,
            confidence=confidence,
            relationships=relationships,
            keywords=keywords,
            agent=agent,
        )
        duplicates = self.search(
            query=clean_text,
            scope=scope,
            agent=agent or None,
            include_deprecated=True,
            limit=5,
        )["entries"]
        proposal_id = "prop_" + uuid.uuid4().hex[:16]
        warnings = ["text_redacted"] if redacted else []
        proposal = {
            "schema_version": PROPOSAL_SCHEMA_VERSION,
            "id": proposal_id,
            "status": "pending",
            "action": "add",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "entry": {"record": record},
            "duplicate_matches": duplicates,
            "warnings": warnings,
        }
        self._write_proposal(proposal)
        return proposal

    def _proposal_path(self, proposal_id: str) -> Path:
        if not proposal_id.startswith("prop_"):
            raise MemoryStoreError("INVALID_PROPOSAL_ID", "Proposal id must start with 'prop_'")
        return self.proposal_dir() / f"{proposal_id}.json"

    def _write_proposal(self, proposal: dict[str, Any]) -> None:
        _atomic_write(
            self._proposal_path(str(proposal["id"])),
            json.dumps(proposal, indent=2, sort_keys=True) + "\n",
        )

    def get_proposal(self, proposal_id: str) -> dict[str, Any]:
        path = self._proposal_path(proposal_id)
        try:
            proposal = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise MemoryStoreError(
                "PROPOSAL_NOT_FOUND", f"No proposal found for '{proposal_id}'"
            ) from exc
        except json.JSONDecodeError as exc:
            raise MemoryStoreError(
                "PROPOSAL_INVALID", f"Proposal '{proposal_id}' is invalid JSON"
            ) from exc
        if (
            not isinstance(proposal, dict)
            or proposal.get("schema_version") != PROPOSAL_SCHEMA_VERSION
        ):
            raise MemoryStoreError(
                "PROPOSAL_INVALID", f"Proposal '{proposal_id}' has invalid schema"
            )
        return proposal

    def approve(self, proposal_id: str) -> dict[str, Any]:
        proposal = self.get_proposal(proposal_id)
        if proposal.get("status") != "pending":
            raise MemoryStoreError("PROPOSAL_NOT_PENDING", "Only pending proposals can be approved")
        entry = proposal.get("entry", {})
        record = entry.get("record") if isinstance(entry, dict) else None
        if not isinstance(record, dict):
            raise MemoryStoreError("PROPOSAL_INVALID", "Proposal does not contain a record")
        written = self.record(record)
        proposal = dict(proposal)
        proposal["status"] = "approved"
        proposal["updated_at"] = now_iso()
        proposal["approved_entry"] = written
        self._write_proposal(proposal)
        return proposal

    def reject(self, proposal_id: str, reason: str = "") -> dict[str, Any]:
        proposal = self.get_proposal(proposal_id)
        if proposal.get("status") != "pending":
            raise MemoryStoreError("PROPOSAL_NOT_PENDING", "Only pending proposals can be rejected")
        proposal = dict(proposal)
        proposal["status"] = "rejected"
        proposal["updated_at"] = now_iso()
        if reason:
            proposal["rejection_reason"] = reason
        self._write_proposal(proposal)
        return proposal

    def context(
        self,
        *,
        scope: str | None = None,
        max_chars: int | None = None,
        include_deprecated: bool = False,
        query: str = "",
    ) -> dict[str, Any]:
        configured = self.config.get("mcp", {}).get(
            "default_context_chars",
            self.config.get("memory", {}).get("max_injection_chars", 12000),
        )
        budget = max_chars if isinstance(max_chars, int) and max_chars > 0 else int(configured)
        candidates = self.search(
            query=query,
            scope=scope,
            include_deprecated=include_deprecated,
            limit=1000,
        )["entries"]
        header = "AI MEMORY (aimem MCP, budgeted and ranked)"
        used = len(header)
        lines = [header]
        included: list[dict[str, Any]] = []
        omitted: list[dict[str, Any]] = []
        for entry in candidates:
            record = entry.get("record") or {}
            text = str(record.get("text") or normalize_entry_text(str(entry.get("text", ""))))
            block = f"\n- [{entry['scope']}] {entry['section']}: {text} ({entry['id']})"
            if used + len(block) > budget:
                omitted.append({"id": entry.get("id"), "reason": "budget_exceeded"})
                continue
            lines.append(block[1:])
            used += len(block)
            included.append(entry)
        return {
            "context": "\n".join(lines) + ("\n" if included else ""),
            "entries": included,
            "omitted": omitted,
            "budget": {"max_chars": budget, "used_chars": used, "omitted_count": len(omitted)},
            "ranking": "match score, priority, validation status, scope, then file order",
        }

    def handoff(
        self,
        *,
        record_id: str,
        to_scope: str,
        topic: str = "",
        reason: str = "",
        agent: str = "",
    ) -> dict[str, Any]:
        source = self.get(record_id)
        source_record = source.get("record") or {}
        target_topic = topic or str(source.get("section") or "Handoffs")
        relationships = [{"type": "promoted_from", "id": record_id}]
        if reason:
            reason_id = stable_record_id("session", reason, "note", reason)
            relationships.append({"type": "handoff_reason", "id": reason_id})
        return self.propose(
            scope=to_scope,
            topic=target_topic,
            text=str(
                source_record.get("text") or normalize_entry_text(str(source.get("text", "")))
            ),
            kind=str(source_record.get("kind", "fact")),
            priority=str(source_record.get("priority", "medium")),
            evidence=list(source_record.get("evidence", ["agent_inferred"])),
            validation_status=str(source_record.get("validation_status", "needs_review")),
            source="mcp_handoff",
            relationships=relationships,
            keywords=list(source_record.get("keywords", [])),
            agent=agent,
        )

    def conflicts(self, *, scope: str | None = None) -> dict[str, Any]:
        entries = self.entries(scope=scope, include_deprecated=True)
        by_id = {entry.id: entry for entry in entries if entry.id}
        clusters: list[dict[str, Any]] = []
        for entry in entries:
            record = entry.record or {}
            for relation in record.get("relationships", []):
                if relation.get("type") in CONFLICT_RELATIONSHIPS and relation.get("id") in by_id:
                    clusters.append(
                        {
                            "type": "explicit_relationship",
                            "relationship": relation.get("type"),
                            "entries": [entry.to_dict(), by_id[relation["id"]].to_dict()],
                            "explanation": (
                                "Conflict or supersession is explicitly recorded in "
                                "memory metadata."
                            ),
                        }
                    )
        grouped: dict[tuple[str, str, str], list[MemoryEntry]] = {}
        for entry in entries:
            record = entry.record or {}
            text = normalize_entry_text(str(record.get("text") or entry.text)).lower()
            key = (entry.scope, entry.section, text)
            grouped.setdefault(key, []).append(entry)
        for group in grouped.values():
            ids = {entry.id for entry in group}
            if len(group) > 1 and len(ids) > 1:
                clusters.append(
                    {
                        "type": "duplicate_text",
                        "entries": [entry.to_dict() for entry in group],
                        "explanation": (
                            "Entries have the same normalized text in the same scope and section."
                        ),
                    }
                )
        return {"conflicts": clusters, "total": len(clusters)}


def resolve_project_root(directory: str | os.PathLike[str] | None = None) -> Path:
    starts: list[Path] = []
    if directory:
        starts.append(Path(directory))
    env_root = os.environ.get("AIMEM_PROJECT_DIR")
    if env_root:
        starts.append(Path(env_root))
    starts.append(Path.cwd())
    for start in starts:
        candidate = start.resolve()
        for root in (candidate, *candidate.parents):
            if (root / paths.CONFIG_FILE).is_file():
                return root
    raise MemoryStoreError("CONFIG_NOT_FOUND", "Could not find .aimem/config.json")
