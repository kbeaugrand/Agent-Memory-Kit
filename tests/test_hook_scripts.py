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
    "manage_memory.py",
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


def test_record_writes_structured_schema_and_list_queries(make_project, run_hook) -> None:
    root = make_project("--both")
    result = run_hook(
        root,
        "record_memory.py",
        "--scope",
        "project",
        "--topic",
        "Commands",
        "--text",
        "Use pytest for tests",
        "--kind",
        "command",
        "--source",
        "README.md",
        "--confidence",
        "0.9",
        "--valid-from",
        "2026-07-12T00:00:00Z",
        "--relationship",
        "supersedes:mem_old",
        "--no-timestamp",
    )
    assert result.returncode == 0

    raw = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    assert "<!-- aimem:record" in raw

    listing = run_hook(
        root,
        "manage_memory.py",
        "list",
        "--scope",
        "project",
        "--kind",
        "command",
        "--source",
        "README.md",
        "--format",
        "json",
    )
    rows = json.loads(listing.stdout)
    assert len(rows) == 1
    record = rows[0]["record"]
    assert record["schema_version"] == 1
    assert record["scope"] == "project"
    assert record["kind"] == "command"
    assert record["status"] == "active"
    assert record["source"] == "README.md"
    assert record["confidence"] == 0.9
    assert record["validity"] == {"from": "2026-07-12T00:00:00Z", "until": None}
    assert record["relationships"] == [{"type": "supersedes", "id": "mem_old"}]


def test_record_rejects_invalid_schema_values(make_project, run_hook) -> None:
    root = make_project("--both")
    result = run_hook(
        root,
        "record_memory.py",
        "--scope",
        "project",
        "--topic",
        "Commands",
        "--text",
        "Bad confidence",
        "--confidence",
        "2",
    )
    assert result.returncode == 2
    assert "invalid memory record" in result.stderr


def test_consolidate_deduplicates(make_project, run_hook) -> None:
    root = make_project("--both")
    project_memory = root / ".aimem/memory/project.md"
    project_memory.write_text("# Project Memory\n\n## Commands\n- a\n- a\n- b\n", encoding="utf-8")
    result = run_hook(root, "consolidate_memory.py")
    assert result.returncode == 0
    text = project_memory.read_text(encoding="utf-8")
    assert text.count("- a") == 1
    assert "- b" in text


def test_manage_migrate_converts_legacy_markdown(make_project, run_hook) -> None:
    root = make_project("--both")
    project_memory = root / ".aimem/memory/project.md"
    project_memory.write_text(
        "# Project Memory\n\n## Commands\n- legacy command\n- [DEPRECATED] old command\n",
        encoding="utf-8",
    )

    result = run_hook(root, "manage_memory.py", "migrate", "--scope", "project")
    assert result.returncode == 0
    text = project_memory.read_text(encoding="utf-8")
    assert text.count("<!-- aimem:record") == 2
    assert "legacy command" in text
    assert "[DEPRECATED] old command" in text

    listing = run_hook(
        root,
        "manage_memory.py",
        "list",
        "--scope",
        "project",
        "--status",
        "deprecated",
        "--format",
        "json",
    )
    rows = json.loads(listing.stdout)
    assert len(rows) == 1
    assert rows[0]["record"]["source"] == "migration"
    assert rows[0]["record"]["status"] == "deprecated"


def _record(run_hook, root, *pairs: str):
    return run_hook(root, "record_memory.py", *pairs, "--no-timestamp")


def test_manage_list_addresses_entries(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(run_hook, root, "--scope", "project", "--topic", "Commands", "--text", "Run pytest")
    result = run_hook(root, "manage_memory.py", "list", "--scope", "project")
    assert result.returncode == 0
    assert "Commands" in result.stdout
    assert "[1]" in result.stdout
    assert "Run pytest" in result.stdout


def test_manage_delete_removes_entry(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(run_hook, root, "--scope", "project", "--topic", "Gotchas", "--text", "First note")
    _record(run_hook, root, "--scope", "project", "--topic", "Gotchas", "--text", "Second note")
    result = run_hook(
        root,
        "manage_memory.py",
        "delete",
        "--scope",
        "project",
        "--section",
        "Gotchas",
        "--index",
        "1",
    )
    assert result.returncode == 0
    body = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    assert "First note" not in body
    assert "Second note" in body


def test_manage_delete_by_match(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(run_hook, root, "--scope", "project", "--topic", "Gotchas", "--text", "obsolete hack")
    result = run_hook(
        root, "manage_memory.py", "delete", "--scope", "project", "--match", "obsolete"
    )
    assert result.returncode == 0
    assert "obsolete hack" not in (root / ".aimem/memory/project.md").read_text(encoding="utf-8")


def test_deprecate_hides_from_injection_then_restore(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(run_hook, root, "--scope", "project", "--topic", "Gotchas", "--text", "Flaky note")

    run_hook(
        root,
        "manage_memory.py",
        "deprecate",
        "--scope",
        "project",
        "--section",
        "Gotchas",
        "--index",
        "1",
    )
    body = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    assert "[DEPRECATED] Flaky note" in body  # retained on disk

    hidden = run_hook(root, "inject_memory.py", "--format", "text")
    assert "Flaky note" not in hidden.stdout  # excluded from injected context

    run_hook(
        root,
        "manage_memory.py",
        "restore",
        "--scope",
        "project",
        "--section",
        "Gotchas",
        "--index",
        "1",
    )
    shown = run_hook(root, "inject_memory.py", "--format", "text")
    assert "Flaky note" in shown.stdout


def test_consolidate_preserves_deprecated(make_project, run_hook) -> None:
    root = make_project("--both")
    project_memory = root / ".aimem/memory/project.md"
    project_memory.write_text(
        "# Project Memory\n\n## Commands\n- [DEPRECATED] old command\n- keep me\n- keep me\n",
        encoding="utf-8",
    )
    result = run_hook(root, "consolidate_memory.py")
    assert result.returncode == 0
    text = project_memory.read_text(encoding="utf-8")
    assert "[DEPRECATED] old command" in text
    assert text.count("- keep me") == 1


def test_record_agent_scope_writes_agent_file(make_project, run_hook) -> None:
    root = make_project("--both")
    result = _record(
        run_hook,
        root,
        "--scope",
        "agent",
        "--agent",
        "Dev",
        "--topic",
        "Conventions",
        "--text",
        "Prefers TDD",
    )
    assert result.returncode == 0
    agent_file = root / ".aimem/memory/agents/Dev.md"
    assert agent_file.is_file()
    assert "Prefers TDD" in agent_file.read_text(encoding="utf-8")


def test_record_agent_scope_requires_name(make_project, run_hook) -> None:
    root = make_project("--both")
    result = _record(
        run_hook, root, "--scope", "agent", "--topic", "Conventions", "--text", "no agent given"
    )
    assert result.returncode == 2


def test_manage_agent_scope_list(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(
        run_hook,
        root,
        "--scope",
        "agent",
        "--agent",
        "Dev",
        "--topic",
        "Conventions",
        "--text",
        "Prefers TDD",
    )
    result = run_hook(root, "manage_memory.py", "list", "--scope", "agent", "--agent", "Dev")
    assert result.returncode == 0
    assert "Prefers TDD" in result.stdout


def test_agent_memory_not_injected_by_default(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(
        run_hook,
        root,
        "--scope",
        "agent",
        "--agent",
        "Dev",
        "--topic",
        "Conventions",
        "--text",
        "Agent only fact",
    )
    result = run_hook(root, "inject_memory.py", "--format", "text")
    assert "Agent only fact" not in result.stdout


def test_inject_size_nudge_when_over_budget(make_project, run_hook) -> None:
    root = make_project("--both")
    config_path = root / ".aimem/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["memory"]["max_injection_chars"] = 50
    config_path.write_text(json.dumps(config), encoding="utf-8")

    _record(
        run_hook,
        root,
        "--scope",
        "project",
        "--topic",
        "Commands",
        "--text",
        "A note long enough to exceed the tiny injection budget set above",
    )
    result = run_hook(root, "inject_memory.py", "--format", "text")
    assert "injected memory is large" in result.stdout


def test_record_warns_when_section_grows(make_project, run_hook) -> None:
    root = make_project("--both")
    config_path = root / ".aimem/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["memory"]["warn_entries_per_section"] = 1
    config_path.write_text(json.dumps(config), encoding="utf-8")

    _record(run_hook, root, "--scope", "project", "--topic", "Commands", "--text", "first")
    result = _record(
        run_hook, root, "--scope", "project", "--topic", "Commands", "--text", "second"
    )
    assert "active entries" in result.stderr
