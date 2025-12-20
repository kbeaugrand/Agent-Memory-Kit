"""Tests validating the structure of the generated Kiro and Copilot artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from aimem.cli import main


def _init(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--both", "--no-input"]) == 0
    return root


def test_kiro_hook_is_valid(tmp_path: Path) -> None:
    root = _init(tmp_path)
    data = json.loads((root / ".kiro/hooks/aimem-memory.kiro.hook").read_text(encoding="utf-8"))
    assert data["version"] == "v1"
    triggers = {hook["trigger"] for hook in data["hooks"]}
    assert {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostFileSave", "Stop"} <= triggers


def test_copilot_hook_is_valid(tmp_path: Path) -> None:
    root = _init(tmp_path)
    data = json.loads((root / ".github/hooks/aimem-memory.json").read_text(encoding="utf-8"))
    assert set(data["hooks"]) >= {"SessionStart", "PreToolUse", "PostToolUse"}
    session = data["hooks"]["SessionStart"][0]
    assert session["type"] == "command"
    assert "windows" in session


def test_copilot_instructions_have_applyto(tmp_path: Path) -> None:
    root = _init(tmp_path)
    text = (root / ".github/instructions/aimem-memory.instructions.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r'applyTo:\s*"\*\*"', text)


def test_kiro_steering_declares_inclusion(tmp_path: Path) -> None:
    root = _init(tmp_path)
    text = (root / ".kiro/steering/aimem-memory.md").read_text(encoding="utf-8")
    assert "inclusion: always" in text


def test_agents_have_frontmatter(tmp_path: Path) -> None:
    root = _init(tmp_path)
    assert (
        (root / ".kiro/agents/memory-initializer.md").read_text(encoding="utf-8").startswith("---")
    )
    assert (root / ".kiro/agents/memory-curator.md").read_text(encoding="utf-8").startswith("---")
    initializer = (root / ".github/agents/memory-initializer.agent.md").read_text(encoding="utf-8")
    assert "name: memory-initializer" in initializer
    copilot = (root / ".github/agents/memory-curator.agent.md").read_text(encoding="utf-8")
    assert "name: memory-curator" in copilot


def test_no_unresolved_template_tokens(tmp_path: Path) -> None:
    root = _init(tmp_path)
    for path in root.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "{{" not in text, path
