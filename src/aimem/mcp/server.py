"""MCP server wiring for aimem memory."""

from __future__ import annotations

import json
from typing import Any

from aimem.core.memory_store import MemoryStore, MemoryStoreError

ENVELOPE_SCHEMA_VERSION = 1


def _ok(data: dict[str, Any], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "ok": True,
        "data": data,
        "warnings": warnings or [],
        "error": None,
    }


def _error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, MemoryStoreError):
        code = exc.code
        message = exc.message
    else:
        code = "INTERNAL_ERROR"
        message = str(exc)
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "ok": False,
        "data": {},
        "warnings": [],
        "error": {"code": code, "message": message},
    }


def _as_list(value: list[str] | None) -> list[str] | None:
    return value if value else None


def _relationships(value: list[dict[str, str]] | None) -> list[dict[str, str]] | None:
    return value if value else None


def create_app(directory: str | None = None) -> Any:
    """Create a FastMCP app with all aimem memory tools registered."""
    from mcp.server.fastmcp import FastMCP

    store = MemoryStore.from_directory(directory)
    store.load_vector_database()
    app = FastMCP(
        "aimem",
        instructions=(
            "Expose Agent Memory Kit as provider-neutral tools and resources. "
            "Durable writes require memory_propose followed by memory_approve."
        ),
    )

    @app.tool(description="Search aimem memory entries with metadata filters.")
    def memory_search(
        query: str = "",
        scope: str | None = None,
        agent: str | None = None,
        include_deprecated: bool = False,
        kind: str | None = None,
        priority: str | None = None,
        validation_status: str | None = None,
        keyword: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        try:
            return _ok(
                store.search(
                    query=query,
                    scope=scope,
                    agent=agent,
                    include_deprecated=include_deprecated,
                    kind=kind,
                    priority=priority,
                    validation_status=validation_status,
                    keyword=keyword,
                    limit=limit,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Get one aimem memory entry by stable memory id.")
    def memory_get(record_id: str) -> dict[str, Any]:
        try:
            return _ok({"entry": store.get(record_id)})
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Create a pending memory proposal without activating it.")
    def memory_propose(
        scope: str,
        topic: str,
        text: str,
        kind: str = "fact",
        priority: str = "medium",
        evidence: list[str] | None = None,
        validation_status: str = "needs_review",
        source: str = "mcp",
        verified_from: list[str] | None = None,
        confidence: float = 0.8,
        relationships: list[dict[str, str]] | None = None,
        keywords: list[str] | None = None,
        agent: str = "",
    ) -> dict[str, Any]:
        try:
            proposal = store.propose(
                scope=scope,
                topic=topic,
                text=text,
                kind=kind,
                priority=priority,
                evidence=_as_list(evidence),
                validation_status=validation_status,
                source=source,
                verified_from=_as_list(verified_from),
                confidence=confidence,
                relationships=_relationships(relationships),
                keywords=_as_list(keywords),
                agent=agent,
            )
            return _ok({"proposal": proposal}, warnings=list(proposal.get("warnings", [])))
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Approve a pending memory proposal and write it to active memory.")
    def memory_approve(proposal_id: str) -> dict[str, Any]:
        try:
            return _ok({"proposal": store.approve(proposal_id)})
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Reject a pending memory proposal.")
    def memory_reject(proposal_id: str, reason: str = "") -> dict[str, Any]:
        try:
            return _ok({"proposal": store.reject(proposal_id, reason)})
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Return explainable, strictly budgeted memory context.")
    def memory_context(
        scope: str | None = None,
        max_chars: int | None = None,
        include_deprecated: bool = False,
        query: str = "",
    ) -> dict[str, Any]:
        try:
            return _ok(
                store.context(
                    scope=scope,
                    max_chars=max_chars,
                    include_deprecated=include_deprecated,
                    query=query,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Create a proposal to hand off or promote an entry into another scope.")
    def memory_handoff(
        record_id: str,
        to_scope: str,
        topic: str = "",
        reason: str = "",
        agent: str = "",
    ) -> dict[str, Any]:
        try:
            return _ok(
                {
                    "proposal": store.handoff(
                        record_id=record_id,
                        to_scope=to_scope,
                        topic=topic,
                        reason=reason,
                        agent=agent,
                    )
                }
            )
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.tool(description="Find explicit and explainable memory conflicts.")
    def memory_conflicts(scope: str | None = None) -> dict[str, Any]:
        try:
            return _ok(store.conflicts(scope=scope))
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return _error(exc)

    @app.resource("aimem://context", mime_type="application/json")
    def context_resource() -> str:
        return json.dumps(_ok(store.context()), sort_keys=True)

    @app.resource("aimem://entry/{record_id}", mime_type="application/json")
    def entry_resource(record_id: str) -> str:
        try:
            return json.dumps(_ok({"entry": store.get(record_id)}), sort_keys=True)
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return json.dumps(_error(exc), sort_keys=True)

    @app.resource("aimem://proposal/{proposal_id}", mime_type="application/json")
    def proposal_resource(proposal_id: str) -> str:
        try:
            return json.dumps(_ok({"proposal": store.get_proposal(proposal_id)}), sort_keys=True)
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return json.dumps(_error(exc), sort_keys=True)

    @app.resource("aimem://scope/{scope}", mime_type="application/json")
    def scope_resource(scope: str) -> str:
        try:
            return json.dumps(_ok(store.search(scope=scope, limit=1000)), sort_keys=True)
        except Exception as exc:  # pragma: no cover - exercised through MCP clients
            return json.dumps(_error(exc), sort_keys=True)

    return app


def run_server(*, directory: str | None = None, transport: str = "stdio") -> None:
    """Run the aimem MCP server."""
    app = create_app(directory)
    app.run(transport=transport)
