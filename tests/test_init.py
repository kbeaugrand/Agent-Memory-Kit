"""Tests for the init command's platform-native generated files."""

from __future__ import annotations

from pathlib import Path

from aimem.cli import main

EXPECTED = [
    ".kiro/steering/product.md",
    ".kiro/steering/tech.md",
    ".kiro/steering/structure.md",
    ".kiro/skills/lesson-learning/SKILL.md",
    ".kiro/agents/generate-project-instructions.md",
    ".kiro/hooks/lesson-learning.kiro.hook",
    ".github/copilot-instructions.md",
    ".github/skills/lesson-learning/SKILL.md",
    ".github/agents/generate-project-instructions.agent.md",
    ".github/hooks/lesson-learning.json",
]


def test_generates_only_platform_native_files(make_project) -> None:
    root = make_project("--both")
    assert sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    ) == sorted(EXPECTED)
    assert not (root / ".aimem").exists()


def test_kiro_only(make_project) -> None:
    root = make_project("--kiro")
    assert (root / ".kiro/steering/product.md").is_file()
    assert not (root / ".kiro/steering/aimem-memory.md").exists()
    assert not (root / ".github").exists()
    assert not (root / ".aimem").exists()


def test_copilot_only(make_project) -> None:
    root = make_project("--copilot")
    assert (root / ".github/copilot-instructions.md").is_file()
    assert not (root / ".github/instructions/aimem-memory.instructions.md").exists()
    assert not (root / ".kiro").exists()
    assert not (root / ".aimem").exists()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--both", "--no-input", "--dry-run"]) == 0
    assert list(root.iterdir()) == []
