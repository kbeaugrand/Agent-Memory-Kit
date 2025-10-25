"""Read/write the aimem manifest that tracks generated files for idempotent updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class Manifest:
    """Tracks the write mode, content hash, and template version of each managed file."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data: dict[str, Any] = data or {"schema_version": SCHEMA_VERSION, "files": {}}
        self._data.setdefault("files", {})

    @classmethod
    def load(cls, path: Path) -> Manifest:
        """Load a manifest from ``path``; return an empty manifest on any error."""
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return cls()
            if isinstance(raw, dict):
                return cls(raw)
        return cls()

    def entry(self, key: str) -> dict[str, Any] | None:
        """Return the recorded entry for ``key`` (a project-relative path), or ``None``."""
        files = self._data.get("files", {})
        value = files.get(key)
        return value if isinstance(value, dict) else None

    def set_entry(self, key: str, mode: str, content_hash: str, template_version: str) -> None:
        """Record or update the entry for ``key``."""
        self._data.setdefault("files", {})[key] = {
            "mode": mode,
            "hash": content_hash,
            "template_version": template_version,
        }

    def keys(self) -> list[str]:
        """Return all tracked file keys."""
        return list(self._data.get("files", {}).keys())

    def save(self, path: Path, *, aimem_version: str, generated_at: str) -> None:
        """Persist the manifest to ``path`` as pretty-printed, deterministic JSON."""
        self._data["schema_version"] = SCHEMA_VERSION
        self._data["aimem_version"] = aimem_version
        self._data["updated_at"] = generated_at
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data, indent=2, sort_keys=True)
        path.write_text(payload + "\n", encoding="utf-8")
