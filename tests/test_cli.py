"""Tests for the CLI surface: the single ``init`` subcommand plus help/version."""

from __future__ import annotations

import pytest

from aimem import __version__
from aimem.cli import main


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_no_arguments_prints_help_and_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage: aimem" in capsys.readouterr().out


def test_unknown_subcommand_is_rejected() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["deploy"])
    assert excinfo.value.code == 2


def test_init_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["init", "--help"])
    assert excinfo.value.code == 0


@pytest.mark.parametrize("other", ["deploy", "sync", "update", "remove"])
def test_other_subcommands_are_rejected(other: str) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([other])
    assert excinfo.value.code == 2
