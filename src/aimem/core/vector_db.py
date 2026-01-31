"""Small local vector database for deterministic memory similarity search."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

VECTOR_SCHEMA_VERSION = 1
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_+\-.]*", re.IGNORECASE)


@dataclass(frozen=True)
class VectorDocument:
    """A persisted vector document."""

    id: str
    text: str
    metadata: dict[str, Any]
    vector: dict[str, float]
    norm: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "metadata": self.metadata,
            "norm": self.norm,
            "text": self.text,
            "vector": self.vector,
        }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".aimem-tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _tokens(text: str) -> list[str]:
    tokens = [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        if len(token) > 4 and token.endswith("s"):
            expanded.append(token[:-1])
    return expanded


def vectorize(text: str) -> tuple[dict[str, float], float]:
    """Create a normalized sparse vector from text using local lexical features."""
    counts: dict[str, float] = {}
    for token in _tokens(text):
        counts[token] = counts.get(token, 0.0) + 1.0
    for token in _tokens(text.replace("_", " ")):
        if len(token) < 5:
            continue
        for index in range(0, len(token) - 2):
            trigram = "#" + token[index : index + 3]
            counts[trigram] = counts.get(trigram, 0.0) + 0.15
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}, 0.0
    return {key: value / norm for key, value in sorted(counts.items())}, 1.0


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    """Return cosine similarity for normalized sparse vectors."""
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


class LocalVectorDatabase:
    """A JSON-backed local vector database for memory entries."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.documents: dict[str, VectorDocument] = {}

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self.documents = {}
            return
        if not isinstance(data, dict) or data.get("schema_version") != VECTOR_SCHEMA_VERSION:
            self.documents = {}
            return
        documents = data.get("documents", [])
        if not isinstance(documents, list):
            self.documents = {}
            return
        loaded: dict[str, VectorDocument] = {}
        for item in documents:
            if not isinstance(item, dict):
                continue
            record_id = item.get("id")
            vector = item.get("vector")
            metadata = item.get("metadata", {})
            if not isinstance(record_id, str) or not isinstance(vector, dict):
                continue
            if not isinstance(metadata, dict):
                metadata = {}
            clean_vector = {
                str(key): float(value)
                for key, value in vector.items()
                if isinstance(value, int | float)
            }
            loaded[record_id] = VectorDocument(
                id=record_id,
                text=str(item.get("text", "")),
                metadata=metadata,
                vector=clean_vector,
                norm=float(item.get("norm", 1.0) or 1.0),
            )
        self.documents = loaded

    def save(self) -> None:
        payload = {
            "documents": [
                document.to_dict()
                for document in sorted(self.documents.values(), key=lambda item: item.id)
            ],
            "schema_version": VECTOR_SCHEMA_VERSION,
        }
        _atomic_write(self.path, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def replace(self, documents: list[tuple[str, str, dict[str, Any]]]) -> None:
        indexed: dict[str, VectorDocument] = {}
        for record_id, text, metadata in documents:
            vector, norm = vectorize(text)
            indexed[record_id] = VectorDocument(
                id=record_id,
                text=text,
                metadata=metadata,
                vector=vector,
                norm=norm,
            )
        self.documents = indexed
        self.save()

    def search(self, query: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        query_vector, _norm = vectorize(query)
        rows: list[dict[str, Any]] = []
        for document in self.documents.values():
            similarity = cosine_similarity(query_vector, document.vector)
            if similarity <= 0:
                continue
            rows.append(
                {
                    "id": document.id,
                    "metadata": document.metadata,
                    "similarity": similarity,
                }
            )
        rows.sort(key=lambda item: (-float(item["similarity"]), str(item["id"])))
        if limit is not None and limit > 0:
            return rows[:limit]
        return rows
