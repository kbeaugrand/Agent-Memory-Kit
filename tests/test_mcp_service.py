"""Tests for the package-level MCP memory service."""

from __future__ import annotations

import json

from aimem.core.memory_store import MemoryStore


def test_memory_propose_approve_search_and_get(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)

    proposal = store.propose(
        scope="project",
        topic="Build and Validation",
        text="Run pytest before changing MCP memory behavior.",
        kind="command",
        priority="critical",
        evidence=["source_code"],
        validation_status="verified",
        source="tests/test_mcp_service.py",
        keywords=["pytest", "mcp"],
    )
    assert proposal["status"] == "pending"
    assert (root / ".aimem/proposals" / f"{proposal['id']}.json").is_file()

    approved = store.approve(proposal["id"])
    entry = approved["approved_entry"]
    assert approved["status"] == "approved"
    assert entry["record"]["kind"] == "command"
    assert entry["record"]["priority"] == "critical"

    search = store.search(query="pytest", scope="project")
    assert search["total"] >= 1
    assert search["entries"][0]["id"] == entry["id"]
    assert search["entries"][0]["match"]["similarity"] > 0
    assert (root / ".aimem/index/vector.json").is_file()

    fetched = store.get(entry["id"])
    assert fetched["record"]["text"] == "Run pytest before changing MCP memory behavior."
    index = json.loads((root / ".aimem/index/project.json").read_text(encoding="utf-8"))
    assert any(record["id"] == entry["id"] for record in index["records"])


def test_memory_reject_keeps_memory_unchanged(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)

    proposal = store.propose(scope="project", topic="Gotchas", text="Do not activate this.")
    rejected = store.reject(proposal["id"], "not durable")

    assert rejected["status"] == "rejected"
    assert "Do not activate this" not in (root / ".aimem/memory/project.md").read_text(
        encoding="utf-8"
    )


def test_vector_database_similarity_ranks_related_memory(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)
    lint_entry = store.approve(
        store.propose(
            scope="project",
            topic="Build and Validation",
            text="Run ruff lint checks before publishing a release.",
            keywords=["ruff", "lint", "release"],
        )["id"]
    )["approved_entry"]
    store.approve(
        store.propose(
            scope="project",
            topic="Architecture",
            text="Memory files use plain Markdown with sidecar JSON metadata.",
        )["id"]
    )

    loaded = store.load_vector_database()
    result = store.search(query="release lint checks", scope="project")

    assert loaded["documents"] >= 2
    assert result["entries"][0]["id"] == lint_entry["id"]
    assert result["entries"][0]["match"]["similarity"] > 0


def test_memory_context_is_budgeted_and_explainable(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)
    first = store.approve(
        store.propose(scope="project", topic="Commands", text="MercuryAlpha uses pytest.")["id"]
    )
    store.approve(
        store.propose(
            scope="project",
            topic="Commands",
            text="MercuryBeta uses ruff for lint checks before release.",
        )["id"]
    )

    context = store.context(scope="project", max_chars=120, query="Mercury")
    assert context["budget"]["max_chars"] == 120
    assert context["budget"]["used_chars"] <= 120
    assert context["budget"]["omitted_count"] >= 1
    assert first["approved_entry"]["id"] in context["context"]
    assert context["ranking"]


def test_memory_handoff_creates_pending_target_proposal(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)
    source = store.approve(
        store.propose(scope="session", topic="Working Notes", text="Promote this later.")["id"]
    )["approved_entry"]

    handoff = store.handoff(record_id=source["id"], to_scope="project", topic="Decisions")

    assert handoff["status"] == "pending"
    record = handoff["entry"]["record"]
    assert record["scope"] == "project"
    assert record["section"] == "Decisions"
    assert {"type": "promoted_from", "id": source["id"]} in record["relationships"]


def test_memory_conflicts_reports_explicit_relationships(make_project) -> None:
    root = make_project("--both")
    store = MemoryStore.from_directory(root)
    first = store.approve(
        store.propose(scope="project", topic="Rules", text="Use command A.")["id"]
    )["approved_entry"]
    store.approve(
        store.propose(
            scope="project",
            topic="Rules",
            text="Use command B.",
            relationships=[{"type": "contradicts", "id": first["id"]}],
        )["id"]
    )

    conflicts = store.conflicts(scope="project")
    assert conflicts["total"] >= 1
    assert conflicts["conflicts"][0]["type"] == "explicit_relationship"