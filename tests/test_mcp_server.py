"""Tests for the aimem MCP server registration surface."""

from __future__ import annotations

import asyncio
import json

from aimem.mcp.server import create_app


def _structured(result):
    if isinstance(result, tuple) and len(result) == 2:
        return result[1]
    return result


def test_mcp_server_registers_memory_tools(make_project) -> None:
    root = make_project("--both")
    app = create_app(str(root))

    assert (root / ".aimem/index/vector.json").is_file()
    tools = {tool.name for tool in asyncio.run(app.list_tools())}

    assert {
        "memory_search",
        "memory_get",
        "memory_propose",
        "memory_approve",
        "memory_reject",
        "memory_context",
        "memory_handoff",
        "memory_conflicts",
    } <= tools


def test_mcp_tool_calls_use_stable_json_envelopes(make_project) -> None:
    root = make_project("--both")
    app = create_app(str(root))

    proposed = _structured(
        asyncio.run(
            app.call_tool(
                "memory_propose",
                {"scope": "project", "topic": "Commands", "text": "Use pytest for MCP tests."},
            )
        )
    )
    assert isinstance(proposed, dict)
    assert proposed["schema_version"] == 1
    assert proposed["ok"] is True
    proposal_id = proposed["data"]["proposal"]["id"]

    approved = _structured(
        asyncio.run(app.call_tool("memory_approve", {"proposal_id": proposal_id}))
    )
    assert isinstance(approved, dict)
    assert approved["ok"] is True
    entry_id = approved["data"]["proposal"]["approved_entry"]["id"]

    fetched = _structured(asyncio.run(app.call_tool("memory_get", {"record_id": entry_id})))
    assert isinstance(fetched, dict)
    assert fetched["ok"] is True
    assert fetched["data"]["entry"]["id"] == entry_id


def test_mcp_resources_are_registered(make_project) -> None:
    root = make_project("--both")
    app = create_app(str(root))

    templates = {
        str(template.uriTemplate) for template in asyncio.run(app.list_resource_templates())
    }
    assert "aimem://entry/{record_id}" in templates
    assert "aimem://proposal/{proposal_id}" in templates
    assert "aimem://scope/{scope}" in templates

    resources = {str(resource.uri) for resource in asyncio.run(app.list_resources())}
    assert "aimem://context" in resources
    context = next(iter(asyncio.run(app.read_resource("aimem://context"))))
    payload = json.loads(context.content)
    assert payload["schema_version"] == 1
    assert payload["ok"] is True
