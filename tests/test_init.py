"""Tests for the init command's generated tree and options."""

from __future__ import annotations

import json
from pathlib import Path

from aimem.cli import main

EXPECTED = [
    ".aimem/config.json",
    ".aimem/manifest.json",
    ".aimem/hooks/_common.py",
    ".aimem/hooks/inject_memory.py",
    ".aimem/hooks/record_memory.py",
    ".aimem/hooks/consolidate_memory.py",
    ".aimem/hooks/guard_memory.py",
    ".aimem/memory/project.md",
    ".aimem/memory/session/current.md",
    "AGENTS.md",
    ".gitignore",
    ".kiro/steering/aimem-memory.md",
    ".kiro/steering/product.md",
    ".kiro/agents/memory-curator.md",
    ".kiro/hooks/aimem-memory.kiro.hook",
    ".github/copilot-instructions.md",
    ".github/instructions/aimem-memory.instructions.md",
    ".github/agents/memory-curator.agent.md",
    ".github/hooks/aimem-memory.json",
]


def test_generates_full_tree(make_project) -> None:
    root = make_project("--both")
    for rel in EXPECTED:
        assert (root / rel).is_file(), rel


def test_kiro_only(make_project) -> None:
    root = make_project("--kiro")
    assert (root / ".kiro").is_dir()
    assert not (root / ".github").exists()


def test_copilot_only(make_project) -> None:
    root = make_project("--copilot")
    assert (root / ".github").is_dir()
    assert not (root / ".kiro").exists()


def test_config_reflects_selection(make_project) -> None:
    root = make_project("--both")
    config = json.loads((root / ".aimem/config.json").read_text(encoding="utf-8"))
    assert config["toolchains"] == {"kiro": True, "copilot": True}
    assert config["scopes"]["user"]["enabled"] is False
    assert config["python_command"] == "python3"


def test_python_command_override(make_project) -> None:
    root = make_project("--both", "--python-command", "py -3")
    config = json.loads((root / ".aimem/config.json").read_text(encoding="utf-8"))
    assert config["python_command"] == "py -3"
    hook = (root / ".kiro/hooks/aimem-memory.kiro.hook").read_text(encoding="utf-8")
    assert "py -3 .aimem/hooks/inject_memory.py" in hook


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--both", "--no-input", "--dry-run"]) == 0
    assert not (root / ".aimem").exists()


def test_user_scope_writes_home(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--both", "--no-input", "--user"]) == 0
    assert (home / ".aimem/memory/user.md").is_file()
    config = json.loads((root / ".aimem/config.json").read_text(encoding="utf-8"))
    assert config["scopes"]["user"]["enabled"] is True
