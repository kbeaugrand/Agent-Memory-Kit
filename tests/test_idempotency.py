"""Tests for idempotency, backups, and preservation of user edits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aimem.cli import main


def _init(root: Path, *args: str) -> None:
    assert main(["init", "-C", str(root), "--no-input", *args]) == 0


def _snapshot(root: Path) -> dict[str, str]:
    snapshot = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot[path.relative_to(root).as_posix()] = digest
    return snapshot


def test_rerun_is_noop(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")
    first = _snapshot(root)
    _init(root, "--both")
    assert _snapshot(root) == first


def test_managed_file_modification_is_backed_up(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    target = root / ".aimem/hooks/inject_memory.py"
    original = target.read_text(encoding="utf-8")
    target.write_text(original + "\n# local tweak\n", encoding="utf-8")

    _init(root, "--both")

    assert target.read_text(encoding="utf-8") == original
    backups = list((root / ".aimem/backups").rglob("*inject_memory.py"))
    assert backups
    assert "# local tweak" in backups[0].read_text(encoding="utf-8")


def test_seed_file_is_preserved(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    project_memory = root / ".aimem/memory/project.md"
    project_memory.write_text("# My own notes\n", encoding="utf-8")

    _init(root, "--both")
    assert project_memory.read_text(encoding="utf-8") == "# My own notes\n"


def test_shared_block_preserves_surrounding(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    agents = root / "AGENTS.md"
    content = agents.read_text(encoding="utf-8")
    agents.write_text(f"# Heading\n\n{content}\n## Extra\nkeep me\n", encoding="utf-8")

    _init(root, "--both")
    updated = agents.read_text(encoding="utf-8")
    assert "# Heading" in updated
    assert "keep me" in updated
    assert "AIMEM:BEGIN" in updated


def test_user_owned_coding_rules_survive_rerun(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    _init(root, "--both")

    copilot_rules = root / ".github/instructions/python-rules.instructions.md"
    kiro_rules = root / ".kiro/steering/python-rules.md"
    copilot_rules.write_text(
        '---\napplyTo: "**/*.py"\n---\n\nRun focused tests after Python edits.\n',
        encoding="utf-8",
    )
    kiro_rules.write_text(
        "---\ninclusion: fileMatch\nfileMatchPattern: '**/*.py'\n---\n\n"
        "Run focused tests after Python edits.\n",
        encoding="utf-8",
    )

    before = {path: path.read_text(encoding="utf-8") for path in (copilot_rules, kiro_rules)}
    _init(root, "--both")
    assert {path: path.read_text(encoding="utf-8") for path in before} == before


def test_mcp_config_merge_preserves_other_servers(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    config_path = root / ".vscode/mcp.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "inputs": [{"id": "token", "type": "promptString"}],
                "servers": {"otherServer": {"command": "other", "args": []}},
            }
        ),
        encoding="utf-8",
    )

    _init(root, "--both")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data["inputs"] == [{"id": "token", "type": "promptString"}]
    assert data["servers"]["otherServer"] == {"command": "other", "args": []}
    assert data["servers"]["aimem"] == {
        "args": ["mcp-server"],
        "command": "aimem",
        "cwd": "${workspaceFolder}",
        "type": "stdio",
    }
