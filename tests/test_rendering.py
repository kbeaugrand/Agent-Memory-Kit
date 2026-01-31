"""Tests for marker-block rendering."""

from __future__ import annotations

from aimem.core import rendering


def test_merge_creates_block_when_absent() -> None:
    merged = rendering.merge_shared_block(None, "hello")
    assert "AIMEM:BEGIN" in merged
    assert "hello" in merged
    assert "AIMEM:END" in merged


def test_merge_replaces_existing_block_and_is_idempotent() -> None:
    first = rendering.merge_shared_block(None, "one")
    replaced = rendering.merge_shared_block(first, "two")
    assert "two" in replaced
    assert "one" not in replaced
    assert replaced.count("AIMEM:BEGIN") == 1
    # Re-applying the same body must be a no-op.
    assert rendering.merge_shared_block(replaced, "two") == replaced


def test_merge_preserves_surrounding_content() -> None:
    existing = "# Title\n\nUser text before.\n"
    merged = rendering.merge_shared_block(existing, "managed body", comment_style="md")
    assert merged.startswith("# Title")
    assert "User text before." in merged
    assert "managed body" in merged


def test_extract_block_roundtrip() -> None:
    merged = rendering.merge_shared_block(None, "payload")
    block = rendering.extract_block(merged)
    assert block is not None
    assert "payload" in block


def test_hash_style_markers_use_hash_comments() -> None:
    merged = rendering.merge_shared_block(None, "generated", comment_style="hash")
    assert merged.startswith("# AIMEM:BEGIN")
