"""Marker-block rendering helpers for shared instruction files."""

from __future__ import annotations

import re

MARKER_BEGIN = "AIMEM:BEGIN"
MARKER_END = "AIMEM:END"
_BEGIN_NOTE = "managed by aimem — do not edit inside this block; run `aimem init` to update"

_COMMENT_STYLES = {
    "md": ("<!-- {begin} ({note}) -->", "<!-- {end} -->"),
    "hash": ("# {begin} ({note})", "# {end}"),
}


def markers(comment_style: str) -> tuple[str, str]:
    """Return the ``(begin, end)`` marker lines for a comment style (``md`` or ``hash``)."""
    try:
        begin_tmpl, end_tmpl = _COMMENT_STYLES[comment_style]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"unknown comment style: {comment_style!r}") from exc
    begin = begin_tmpl.format(begin=MARKER_BEGIN, note=_BEGIN_NOTE, end=MARKER_END)
    end = end_tmpl.format(begin=MARKER_BEGIN, note=_BEGIN_NOTE, end=MARKER_END)
    return begin, end


def _block_pattern(begin: str, end: str) -> re.Pattern[str]:
    return re.compile(re.escape(begin) + r".*?" + re.escape(end), re.DOTALL)


def build_block(body: str, comment_style: str = "md") -> str:
    """Wrap ``body`` in aimem begin/end markers for the given comment style."""
    begin, end = markers(comment_style)
    return f"{begin}\n{body.strip()}\n{end}"


def extract_block(text: str, comment_style: str = "md") -> str | None:
    """Return the marker-delimited block found in ``text``, or ``None`` if absent."""
    begin, end = markers(comment_style)
    match = _block_pattern(begin, end).search(text)
    return match.group(0) if match else None


def merge_shared_block(existing: str | None, body: str, comment_style: str = "md") -> str:
    """Insert or replace the aimem managed block within ``existing`` content.

    Everything outside the managed block is preserved verbatim. If ``existing`` has no
    managed block, one is appended. If ``existing`` is empty/``None``, the block becomes
    the entire file.
    """
    block = build_block(body, comment_style)
    begin, end = markers(comment_style)

    if existing is None or existing.strip() == "":
        return block + "\n"

    pattern = _block_pattern(begin, end)
    if pattern.search(existing):
        # re.sub would interpret backslashes in the replacement; use a lambda instead.
        return pattern.sub(lambda _match: block, existing, count=1)

    separator = "" if existing.endswith("\n") else "\n"
    return f"{existing}{separator}\n{block}\n"
