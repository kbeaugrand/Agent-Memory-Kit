"""Tests exercising the generated, self-contained hook scripts."""

from __future__ import annotations

import ast
import json
import py_compile

HOOKS = [
    "_common.py",
    "inject_memory.py",
    "record_memory.py",
    "consolidate_memory.py",
    "guard_memory.py",
]


def test_hooks_compile(make_project) -> None:
    root = make_project("--both")
    for name in HOOKS:
        py_compile.compile(str(root / ".aimem/hooks" / name), doraise=True)


def test_hooks_do_not_import_aimem(make_project) -> None:
    root = make_project("--both")
    for name in HOOKS:
        tree = ast.parse((root / ".aimem/hooks" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] != "aimem" for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] != "aimem"


def test_inject_text_mode(make_project, run_hook) -> None:
    root = make_project("--both")
    run_hook(
        root,
        "record_memory.py",
        "--scope",
        "project",
        "--topic",
        "Commands",
        "--text",
        "Use pytest",
    )
    result = run_hook(root, "inject_memory.py", "--format", "text")
    assert result.returncode == 0
    assert "Use pytest" in result.stdout


def test_inject_copilot_mode(make_project, run_hook) -> None:
    root = make_project("--both")
    run_hook(
        root,
        "record_memory.py",
        "--scope",
        "project",
        "--topic",
        "Commands",
        "--text",
        "Use pytest",
    )
    result = run_hook(
        root, "inject_memory.py", "--format", "copilot", "--event", "SessionStart", stdin="{}"
    )
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "Use pytest" in payload["hookSpecificOutput"]["additionalContext"]


def test_guard_blocks_secret_into_memory(make_project, run_hook) -> None:
    root = make_project("--both")
    payload = json.dumps(
        {
            "tool_name": "create_file",
            "tool_input": {
                "filePath": ".aimem/memory/project.md",
                "content": "api_key = sk-abcdef1234567890",
            },
        }
    )
    result = run_hook(root, "guard_memory.py", "--mode", "copilot", stdin=payload)
    decision = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"


def test_guard_allows_secret_outside_memory(make_project, run_hook) -> None:
    root = make_project("--both")
    payload = json.dumps(
        {
            "tool_name": "create_file",
            "tool_input": {"filePath": "src/app.py", "content": "password = hunter2secret"},
        }
    )
    result = run_hook(root, "guard_memory.py", "--mode", "copilot", stdin=payload)
    assert json.loads(result.stdout) == {}


def test_guard_kiro_mode_blocks_with_exit_code(make_project, run_hook) -> None:
    root = make_project("--both")
    payload = json.dumps(
        {
            "tool_input": {
                "filePath": ".aimem/memory/project.md",
                "content": "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            }
        }
    )
    result = run_hook(root, "guard_memory.py", "--mode", "kiro", stdin=payload)
    assert result.returncode == 2


def test_record_deduplicates(make_project, run_hook) -> None:
    root = make_project("--both")
    for _ in range(2):
        run_hook(
            root,
            "record_memory.py",
            "--scope",
            "project",
            "--topic",
            "Gotchas",
            "--text",
            "Same note",
            "--no-timestamp",
        )
    text = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    assert text.count("- Same note") == 1


def test_consolidate_deduplicates(make_project, run_hook) -> None:
    root = make_project("--both")
    project_memory = root / ".aimem/memory/project.md"
    project_memory.write_text("# Project Memory\n\n## Commands\n- a\n- a\n- b\n", encoding="utf-8")
    result = run_hook(root, "consolidate_memory.py")
    assert result.returncode == 0
    text = project_memory.read_text(encoding="utf-8")
    assert text.count("- a") == 1
    assert "- b" in text
