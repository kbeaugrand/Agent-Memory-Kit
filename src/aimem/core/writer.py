"""Apply planned files to disk according to their write mode, updating the manifest.

Three write modes:

* ``SEED`` — user-owned seed content. Created once and never overwritten (unless
  ``force`` is set, in which case the existing file is backed up first).
* ``MANAGED`` — fully aimem-owned. Rewritten when the template changes. If the file was
  modified by the user since aimem last wrote it, the current version is backed up before
  being replaced, so no work is ever lost.
* ``SHARED`` — a file aimem shares with the user (or another tool). Only the aimem
  marker block is inserted/replaced; everything else is preserved verbatim.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from aimem.core import rendering


class WriteMode(str, Enum):
    SEED = "seed"
    MANAGED = "managed"
    SHARED = "shared"
    JSON_MERGE = "json_merge"


class Action(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"
    BACKED_UP = "backed_up"


@dataclass(frozen=True)
class PlannedFile:
    """A single file aimem intends to write."""

    key: str
    """Manifest key: project-relative POSIX path, or a ``~``-prefixed home path."""

    path: Path
    """Absolute filesystem path to write."""

    mode: WriteMode

    content: str
    """Full file content (SEED/MANAGED) or the marker block body (SHARED)."""

    comment_style: str = "md"
    """Marker comment style for SHARED files: ``md`` or ``hash``."""

    json_path: tuple[str, ...] = ()
    """Object path for JSON_MERGE files, for example ``("servers", "aimem")``."""


@dataclass(frozen=True)
class FileResult:
    key: str
    action: Action
    backup: Path | None = None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".aimem-tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _backup(path: Path, key: str, backups_root: Path, timestamp: str) -> Path:
    safe_key = key.replace("~/", "home/").replace("/", "__").replace("\\", "__")
    destination = backups_root / timestamp / safe_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing = _read(path)
    destination.write_text(existing if existing is not None else "", encoding="utf-8")
    return destination


def apply_file(
    planned: PlannedFile,
    manifest_entry: Mapping[str, Any] | None,
    *,
    template_version: str,
    backups_root: Path,
    timestamp: str,
    force: bool,
    dry_run: bool,
) -> tuple[FileResult, str, str]:
    """Apply a single planned file.

    Returns ``(result, mode, recorded_hash)`` where ``recorded_hash`` is the hash the
    manifest should store for this key (empty string if nothing should be recorded).
    """
    if planned.mode is WriteMode.SEED:
        return _apply_seed(
            planned,
            manifest_entry,
            template_version=template_version,
            backups_root=backups_root,
            timestamp=timestamp,
            force=force,
            dry_run=dry_run,
        )
    if planned.mode is WriteMode.MANAGED:
        return _apply_managed(
            planned,
            manifest_entry,
            template_version=template_version,
            backups_root=backups_root,
            timestamp=timestamp,
            force=force,
            dry_run=dry_run,
        )
    if planned.mode is WriteMode.JSON_MERGE:
        return _apply_json_merge(
            planned,
            manifest_entry,
            backups_root=backups_root,
            timestamp=timestamp,
            force=force,
            dry_run=dry_run,
        )
    return _apply_shared(planned, dry_run=dry_run)


def _apply_seed(
    planned: PlannedFile,
    manifest_entry: Mapping[str, Any] | None,
    *,
    template_version: str,
    backups_root: Path,
    timestamp: str,
    force: bool,
    dry_run: bool,
) -> tuple[FileResult, str, str]:
    existing = _read(planned.path)
    if existing is None:
        seed_hash = rendering.sha256_text(planned.content)
        if not dry_run:
            _write(planned.path, planned.content)
        return FileResult(planned.key, Action.CREATED), planned.mode.value, seed_hash

    if force:
        backup = None
        if not dry_run:
            backup = _backup(planned.path, planned.key, backups_root, timestamp)
            _write(planned.path, planned.content)
        seed_hash = rendering.sha256_text(planned.content)
        return FileResult(planned.key, Action.BACKED_UP, backup), planned.mode.value, seed_hash

    # Preserve user content; keep the recorded hash if present, else record what's on disk.
    recorded = manifest_entry.get("hash") if manifest_entry else None
    seed_hash = recorded or rendering.sha256_text(existing)
    return FileResult(planned.key, Action.SKIPPED), planned.mode.value, seed_hash


def _apply_managed(
    planned: PlannedFile,
    manifest_entry: Mapping[str, Any] | None,
    *,
    template_version: str,
    backups_root: Path,
    timestamp: str,
    force: bool,
    dry_run: bool,
) -> tuple[FileResult, str, str]:
    new_hash = rendering.sha256_text(planned.content)
    existing = _read(planned.path)

    if existing is None:
        if not dry_run:
            _write(planned.path, planned.content)
        return FileResult(planned.key, Action.CREATED), planned.mode.value, new_hash

    disk_hash = rendering.sha256_text(existing)
    if disk_hash == new_hash:
        return FileResult(planned.key, Action.UNCHANGED), planned.mode.value, new_hash

    recorded = manifest_entry.get("hash") if manifest_entry else None
    user_modified = recorded is None or recorded != disk_hash

    backup = None
    if user_modified and not force:
        if not dry_run:
            backup = _backup(planned.path, planned.key, backups_root, timestamp)
            _write(planned.path, planned.content)
        return FileResult(planned.key, Action.BACKED_UP, backup), planned.mode.value, new_hash

    if not dry_run:
        _write(planned.path, planned.content)
    return FileResult(planned.key, Action.UPDATED), planned.mode.value, new_hash


def _apply_shared(planned: PlannedFile, *, dry_run: bool) -> tuple[FileResult, str, str]:
    existing = _read(planned.path)
    merged = rendering.merge_shared_block(existing, planned.content, planned.comment_style)
    block = rendering.extract_block(merged, planned.comment_style) or ""
    block_hash = rendering.sha256_text(block)

    if existing is not None and existing == merged:
        return FileResult(planned.key, Action.UNCHANGED), planned.mode.value, block_hash

    action = Action.CREATED if existing is None else Action.UPDATED
    if not dry_run:
        _write(planned.path, merged)
    return FileResult(planned.key, action), planned.mode.value, block_hash


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _format_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _get_nested(data: Mapping[str, Any], path: tuple[str, ...]) -> object | None:
    current: object = data
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current


def _set_nested(data: dict[str, Any], path: tuple[str, ...], value: object) -> None:
    current = data
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = value


def _apply_json_merge(
    planned: PlannedFile,
    manifest_entry: Mapping[str, Any] | None,
    *,
    backups_root: Path,
    timestamp: str,
    force: bool,
    dry_run: bool,
) -> tuple[FileResult, str, str]:
    if not planned.json_path:
        raise ValueError("JSON_MERGE planned files require json_path")

    desired_document = json.loads(planned.content)
    if not isinstance(desired_document, dict):
        raise ValueError("JSON_MERGE content must be a JSON object")
    desired_value = _get_nested(desired_document, planned.json_path)
    if desired_value is None:
        raise ValueError("JSON_MERGE content does not contain json_path")
    desired_hash = rendering.sha256_text(_canonical_json(desired_value))

    existing = _read(planned.path)
    if existing is None:
        if not dry_run:
            _write(planned.path, _format_json(desired_document))
        return FileResult(planned.key, Action.CREATED), planned.mode.value, desired_hash

    try:
        current_document = json.loads(existing)
    except json.JSONDecodeError:
        backup = None
        if not dry_run:
            backup = _backup(planned.path, planned.key, backups_root, timestamp)
            _write(planned.path, _format_json(desired_document))
        return FileResult(planned.key, Action.BACKED_UP, backup), planned.mode.value, desired_hash

    if not isinstance(current_document, dict):
        current_document = {}

    current_value = _get_nested(current_document, planned.json_path)
    if current_value == desired_value:
        return FileResult(planned.key, Action.UNCHANGED), planned.mode.value, desired_hash

    current_hash = rendering.sha256_text(_canonical_json(current_value))
    recorded = manifest_entry.get("hash") if manifest_entry else None
    user_modified = current_value is not None and (recorded is None or recorded != current_hash)

    merged_document = dict(current_document)
    _set_nested(merged_document, planned.json_path, desired_value)

    backup = None
    action = Action.UPDATED
    if user_modified and not force:
        action = Action.BACKED_UP
        if not dry_run:
            backup = _backup(planned.path, planned.key, backups_root, timestamp)
    if not dry_run:
        _write(planned.path, _format_json(merged_document))
    return FileResult(planned.key, action, backup), planned.mode.value, desired_hash
