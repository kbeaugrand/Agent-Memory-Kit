"""Interactive provider selection for ``aimem init``.

All prompts are skippable: callers decide interactivity based on ``--no-input`` and
whether stdin is a TTY. In non-interactive mode these helpers are not called.
"""

from __future__ import annotations


def select_provider() -> str:
    """Ask the user which single provider to configure."""
    print("Which AI provider should aimem configure?")
    print("  [1] Claude Code (default)")
    print("  [2] Kiro")
    print("  [3] GitHub Copilot")
    while True:
        choice = input("Select 1-3 [1]: ").strip() or "1"
        if choice == "1":
            return "claude"
        if choice == "2":
            return "kiro"
        if choice == "3":
            return "copilot"
        print("Please enter 1, 2, or 3.")
