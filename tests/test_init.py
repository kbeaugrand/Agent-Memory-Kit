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
    ".claude/skills/project-knowledge/SKILL.md",
    ".claude/skills/project-knowledge/reference.md",
    ".claude/skills/project-knowledge/examples.md",
    ".claude/skills/lesson-learning/SKILL.md",
    ".claude/agents/generate-project-instructions.md",
    ".claude/settings.json",
]


def test_generates_only_platform_native_files(make_project) -> None:
    root = make_project("--kiro", "--copilot", "--claude")
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


def test_claude_only(make_project) -> None:
    root = make_project("--claude")
    assert (root / ".claude/skills/project-knowledge/SKILL.md").is_file()
    assert (root / ".claude/skills/project-knowledge/reference.md").is_file()
    assert (root / ".claude/skills/project-knowledge/examples.md").is_file()
    assert (root / ".claude/skills/lesson-learning/SKILL.md").is_file()
    assert (root / ".claude/agents/generate-project-instructions.md").is_file()
    assert (root / ".claude/settings.json").is_file()
    assert not (root / ".github").exists()
    assert not (root / ".kiro").exists()
    assert not (root / "CLAUDE.md").exists()
    assert not (root / ".claude/rules").exists()
    assert not (root / ".aimem").exists()


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--claude", "--no-input", "--dry-run"]) == 0
    assert list(root.iterdir()) == []


def test_non_interactive_init_requires_one_provider(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    assert main(["init", "-C", str(root), "--no-input"]) == 1
    assert list(root.iterdir()) == []


def test_multiple_providers_are_rejected() -> None:
    try:
        main(["init", "--kiro", "--claude"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("multiple providers should be rejected")
