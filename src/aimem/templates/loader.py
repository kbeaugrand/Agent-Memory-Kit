"""Load packaged template files as text via :mod:`importlib.resources`."""

from __future__ import annotations

from importlib import resources

_TEMPLATE_PACKAGE = "aimem.templates"


def load_template(relpath: str) -> str:
    """Return the UTF-8 text of a template file addressed by a ``/``-separated path."""
    resource = resources.files(_TEMPLATE_PACKAGE)
    for part in relpath.split("/"):
        resource = resource.joinpath(part)
    return resource.read_text(encoding="utf-8")
