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


def test_generated_instructions_require_memory_approval(tmp_path: Path) -> None:
    root = _init(tmp_path)
    files = [
        root / ".github/instructions/aimem-memory.instructions.md",
        root / ".kiro/steering/aimem-memory.md",
        root / ".github/copilot-instructions.md",
        root / "AGENTS.md",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "Never activate memory silently" in text
        assert "Approval required before activation" in text
        assert "secrets" in text

    detailed = (root / ".github/instructions/aimem-memory.instructions.md").read_text(
        encoding="utf-8"
    )
    assert "Memory candidate detected." in detailed
    assert "Scope: PROJECT | USER | SESSION" in detailed
    assert "full conversation transcripts" in detailed


def test_memory_agents_require_approval_before_durable_writes(tmp_path: Path) -> None:
    root = _init(tmp_path)
    files = [
        root / ".github/agents/memory-curator.agent.md",
        root / ".kiro/agents/memory-curator.md",
        root / ".github/agents/memory-initializer.agent.md",
        root / ".kiro/agents/memory-initializer.md",
    ]

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "explicit approval" in text
        assert "full conversation transcripts" in text
        assert "Never store secrets" in text


def test_memory_template_installed_and_used_by_initializer_agents(tmp_path: Path) -> None:
    root = _init(tmp_path)
    template = (root / ".aimem/memory/TEMPLATE.md").read_text(encoding="utf-8")
    assert "# Memory Template" in template
    assert "## Entry Fields" in template
    assert "## Project Memory Sections" in template
    assert "record_memory.py" in template
    assert "--kind" in template
    assert "--source" in template
    assert "--confidence" in template
    assert "relationships" in template

    for path in (
        root / ".github/agents/memory-initializer.agent.md",
        root / ".kiro/agents/memory-initializer.md",
        root / ".github/instructions/aimem-memory.instructions.md",
        root / ".kiro/steering/aimem-memory.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert ".aimem/memory/TEMPLATE.md" in text
        assert "fill" in text
        assert "memory according" in text


def test_memory_seed_files_define_scope_boundaries(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    root = tmp_path / "proj"
    root.mkdir()
    assert main(["init", "-C", str(root), "--both", "--no-input", "--user"]) == 0

    project = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    session = (root / ".aimem/memory/session/current.md").read_text(encoding="utf-8")
    user = (home / ".aimem/memory/user.md").read_text(encoding="utf-8")

    assert "explicit approval" in project
    assert "temporary plans" in project
    assert "Session memory is not durable memory" in session
    assert "present it as a PROJECT or USER memory candidate" in session
    assert "cross-project preferences" in user
    assert "project-specific facts" in user


def test_generated_guidance_documents_management_and_scopes(tmp_path: Path) -> None:
    root = _init(tmp_path)
    for path in (
        root / ".github/instructions/aimem-memory.instructions.md",
        root / ".kiro/steering/aimem-memory.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "Context vs memory" in text
        assert "manage_memory.py" in text
        assert "Agent memory" in text
        assert "soft-delete" in text

    for path in (
        root / ".github/agents/memory-curator.agent.md",
        root / ".kiro/agents/memory-curator.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "manage_memory.py" in text
        assert "soft-delete" in text


def test_agent_memory_readme_generated(tmp_path: Path) -> None:
    root = _init(tmp_path)
    readme = root / ".aimem/memory/agents/README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "Agent-scoped memory" in text
    assert "--scope agent" in text


def test_config_declares_agent_scope_and_budgets(tmp_path: Path) -> None:
    root = _init(tmp_path)
    config = json.loads((root / ".aimem/config.json").read_text(encoding="utf-8"))
    assert config["scopes"]["agent"]["dir"] == ".aimem/memory/agents"
    assert config["scopes"]["agent"]["inject"] == "none"
    assert config["memory"]["warn_entries_per_section"] > 0
    assert config["memory"]["max_injection_chars"] > 0
    assert config["memory"]["deprecation_marker"] == "[DEPRECATED]"
