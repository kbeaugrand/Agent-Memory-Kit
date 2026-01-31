"""Tests for idempotency and preservation of native project knowledge files."""

from __future__ import annotations

import hashlib
from pathlib import Path

from aimem.cli import main


def _init(root: Path, *args: str) -> None:
    assert main(["init", "-C", str(root), "--no-input", *args]) == 0


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_rerun_is_noop(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")
    first = _snapshot(root)
    _init(root, "--both")
    assert _snapshot(root) == first


def test_seed_files_are_preserved(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    files = (
        root / ".kiro/steering/product.md",
        root / ".github/skills/lesson-learning/SKILL.md",
        root / ".kiro/skills/generate-project-instructions/SKILL.md",
    )
    for path in files:
        path.write_text("user-owned knowledge\n", encoding="utf-8")

    _init(root, "--both")
    for path in files:
        assert path.read_text(encoding="utf-8") == "user-owned knowledge\n"


def test_copilot_managed_block_preserves_surrounding_content(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--copilot")

    instructions = root / ".github/copilot-instructions.md"
    generated = instructions.read_text(encoding="utf-8")
    instructions.write_text(f"# Team Rules\n\n{generated}\nKeep this rule.\n", encoding="utf-8")

    _init(root, "--copilot")
    updated = instructions.read_text(encoding="utf-8")
    assert "# Team Rules" in updated
    assert "Keep this rule." in updated
    assert "AIMEM:BEGIN" in updated


def test_user_owned_native_files_survive_rerun(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    copilot = root / ".github/instructions/python.instructions.md"
    kiro = root / ".kiro/steering/python.md"
    copilot.parent.mkdir(parents=True)
    copilot.write_text('---\napplyTo: "**/*.py"\n---\n\nRun pytest.\n', encoding="utf-8")
    kiro.write_text("---\ninclusion: always\n---\n\nRun pytest.\n", encoding="utf-8")

    before = {path: path.read_text(encoding="utf-8") for path in (copilot, kiro)}
    _init(root, "--both")
    assert {path: path.read_text(encoding="utf-8") for path in before} == before
