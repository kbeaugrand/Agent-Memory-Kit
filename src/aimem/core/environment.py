"""Project environment detection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Environment:
    """Facts about the target project directory."""

    root: Path
    is_git_repo: bool
    has_kiro: bool
    has_copilot: bool
    has_claude: bool


def detect(root: Path) -> Environment:
    """Inspect ``root`` for existing git / Kiro / Copilot configuration."""
    root = root.resolve()
    return Environment(
        root=root,
        is_git_repo=(root / ".git").exists(),
        has_kiro=(root / ".kiro").is_dir(),
        has_copilot=(root / ".github").is_dir(),
        has_claude=(root / ".claude").is_dir(),
    )
