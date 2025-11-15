"""Shared pytest fixtures for the aimem test suite."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from aimem.cli import main

MakeProject = Callable[..., Path]
RunHook = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture
def make_project(tmp_path: Path) -> MakeProject:
    """Return a factory that runs ``aimem init`` into a fresh temp directory."""
    counter = {"n": 0}

    def _make(*args: str) -> Path:
        counter["n"] += 1
        root = tmp_path / f"proj{counter['n']}"
        root.mkdir()
        exit_code = main(["init", "-C", str(root), "--no-input", *args])
        assert exit_code == 0
        return root

    return _make


@pytest.fixture
def run_hook() -> RunHook:
    """Return a helper that runs a generated hook script as a subprocess."""

    def _run(
        root: Path, name: str, *args: str, stdin: str = ""
    ) -> subprocess.CompletedProcess[str]:
        script = root / ".aimem" / "hooks" / name
        return subprocess.run(
            [sys.executable, str(script), *args],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )

    return _run
