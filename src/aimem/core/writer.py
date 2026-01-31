"""Write platform-native project knowledge files."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from aimem.core import rendering


class WriteMode(str, Enum):
    SEED = "seed"
    SHARED = "shared"


class Action(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PlannedFile:
    """A platform-native file aimem intends to seed or update."""

    key: str
    path: Path
    mode: WriteMode
    content: str
    comment_style: str = "md"


@dataclass(frozen=True)
class FileResult:
    key: str
    action: Action


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".aimem-tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def apply_file(planned: PlannedFile, *, dry_run: bool) -> FileResult:
    """Apply a seed file or marker-managed shared block."""
    existing = _read(planned.path)

    if planned.mode is WriteMode.SEED:
        if existing is not None:
            return FileResult(planned.key, Action.SKIPPED)
        if not dry_run:
            _write(planned.path, planned.content)
        return FileResult(planned.key, Action.CREATED)

    merged = rendering.merge_shared_block(existing, planned.content, planned.comment_style)
    if existing == merged:
        return FileResult(planned.key, Action.UNCHANGED)
    if not dry_run:
        _write(planned.path, merged)
    action = Action.CREATED if existing is None else Action.UPDATED
    return FileResult(planned.key, action)
