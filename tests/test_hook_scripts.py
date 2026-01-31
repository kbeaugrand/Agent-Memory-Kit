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
    "learn_session.py",
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
    assert text.count("Same note") == 1
    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert len(index["records"]) == 1


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
        "--priority",
        "critical",
        "--evidence",
        "source_code",
        "--validation-status",
        "verified",
        "--source",
        "README.md",
        "--verified-from",
        "tests/test_hook_scripts.py",
        "--keyword",
        "pytest",
        "--confidence",
        "0.9",
        "--valid-from",
        "2026-07-12T00:00:00Z",
        "--relationship",
        "supersedes:mem_old",
        "--related",
        "mem_related",
        "--no-timestamp",
    )
    assert result.returncode == 0

    raw = (root / ".aimem/memory/project.md").read_text(encoding="utf-8")
    assert "<!-- aimem:record" not in raw
    assert "<!-- aimem:id=" in raw
    assert "🔥 Critical Command: Use pytest for tests" in raw
    assert "Evidence: ✓ Source Code" in raw
    assert "Validation: Verified" in raw
    assert "Verified from: tests/test_hook_scripts.py" in raw
    assert "Keywords: pytest" in raw

    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert index["schema_version"] == 2
    assert len(index["records"]) == 1
    indexed = index["records"][0]

    listing = run_hook(
        root,
        "manage_memory.py",
        "list",
        "--scope",
        "project",
        "--kind",
        "command",
        "--priority",
        "critical",
        "--evidence",
        "source_code",
        "--source",
        "README.md",
        "--format",
        "json",
    )
    rows = json.loads(listing.stdout)
    assert len(rows) == 1
    record = rows[0]["record"]
    assert record == indexed
    assert record["schema_version"] == 2
    assert record["scope"] == "project"
    assert record["section"] == "Commands"
    assert record["kind"] == "command"
    assert record["priority"] == "critical"
    assert record["evidence"] == ["source_code"]
    assert record["validation_status"] == "verified"
    assert record["status"] == "active"
    assert record["source"] == "README.md"
    assert record["verified_from"] == ["tests/test_hook_scripts.py"]
    assert record["keywords"] == ["pytest"]
    assert record["confidence"] == 0.9
    assert record["validity"] == {"from": "2026-07-12T00:00:00Z", "until": None}
    assert record["relationships"] == [
        {"type": "supersedes", "id": "mem_old"},
        {"type": "relates_to", "id": "mem_related"},
    ]
    assert record["text"] == "Use pytest for tests"


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


def test_learn_session_blocks_once_then_allows_learning_stop(make_project, run_hook) -> None:
    root = make_project("--both")
    transcript = root / "transcript.jsonl"
    transcript.write_text("first turn\n", encoding="utf-8")
    payload = json.dumps(
        {"session_id": "session-1", "transcript_path": str(transcript), "hook_event_name": "Stop"}
    )

    first = run_hook(root, "learn_session.py", stdin=payload)
    assert json.loads(first.stdout)["decision"] == "block"

    transcript.write_text("first turn\nlearning turn\n", encoding="utf-8")
    second = run_hook(root, "learn_session.py", stdin=payload)
    assert json.loads(second.stdout) == {}
    duplicate = run_hook(root, "learn_session.py", stdin=payload)
    assert json.loads(duplicate.stdout) == {}


def test_learn_session_retriggers_after_later_turn(make_project, run_hook) -> None:
    root = make_project("--both")
    transcript = root / "transcript.jsonl"
    transcript.write_text("turn one\n", encoding="utf-8")
    payload = json.dumps({"session_id": "session-1", "transcript_path": str(transcript)})
    run_hook(root, "learn_session.py", stdin=payload)
    transcript.write_text("turn one\nlearning\n", encoding="utf-8")
    run_hook(root, "learn_session.py", stdin=payload)

    transcript.write_text("turn one\nlearning\nturn two\n", encoding="utf-8")
    result = run_hook(root, "learn_session.py", stdin=payload)
    assert json.loads(result.stdout)["decision"] == "block"


def test_learn_session_fails_open_and_cleans_up(make_project, run_hook) -> None:
    root = make_project("--both")
    for payload in (
        "not-json",
        "{}",
        json.dumps({"session_id": "x", "transcript_path": "missing"}),
    ):
        result = run_hook(root, "learn_session.py", stdin=payload)
        assert result.returncode == 0
        assert json.loads(result.stdout) == {}

    transcript = root / "transcript.jsonl"
    transcript.write_text("turn\n", encoding="utf-8")
    payload = json.dumps({"session_id": "session-1", "transcript_path": str(transcript)})
    run_hook(root, "learn_session.py", stdin=payload)
    state = root / ".aimem/runtime/lesson-learning.json"
    assert state.is_file()
    cleanup = run_hook(root, "learn_session.py", "--cleanup")
    assert cleanup.returncode == 0
    assert not state.exists()


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
    assert text.count("<!-- aimem:id=") == 2
    assert "<!-- aimem:record" not in text
    assert "legacy command" in text
    assert "[DEPRECATED] old command" in text
    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert len(index["records"]) == 2

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
    assert rows[0]["record"]["validation_status"] == "deprecated"


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
    assert "[DEPRECATED]" in body  # retained on disk
    assert "Flaky note" in body
    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert index["records"][0]["status"] == "deprecated"

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
    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert index["records"][0]["status"] == "active"


def test_inject_orders_priority_before_recency(make_project, run_hook) -> None:
    root = make_project("--both")
    _record(
        run_hook,
        root,
        "--scope",
        "project",
        "--topic",
        "Architecture",
        "--priority",
        "low",
        "--text",
        "Low priority note",
    )
    _record(
        run_hook,
        root,
        "--scope",
        "project",
        "--topic",
        "Architecture",
        "--priority",
        "critical",
        "--evidence",
        "source_code",
        "--validation-status",
        "verified",
        "--text",
        "Critical priority note",
    )

    result = run_hook(root, "inject_memory.py", "--format", "text")
    assert result.returncode == 0
    assert result.stdout.index("Critical priority note") < result.stdout.index("Low priority note")


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
