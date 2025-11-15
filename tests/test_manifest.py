"""Tests for the manifest reader/writer."""

from __future__ import annotations

from pathlib import Path

from aimem.core.manifest import Manifest


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    manifest = Manifest()
    manifest.set_entry("AGENTS.md", "shared", "sha256:abc", "0.1.0")
    manifest.save(path, aimem_version="0.1.0", generated_at="2026-07-11T00:00:00Z")

    loaded = Manifest.load(path)
    entry = loaded.entry("AGENTS.md")
    assert entry is not None
    assert entry["mode"] == "shared"
    assert entry["hash"] == "sha256:abc"


def test_missing_file_yields_empty_manifest(tmp_path: Path) -> None:
    manifest = Manifest.load(tmp_path / "nope.json")
    assert manifest.entry("anything") is None
    assert manifest.keys() == []


def test_invalid_json_yields_empty_manifest(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{ not json", encoding="utf-8")
    assert Manifest.load(path).keys() == []
