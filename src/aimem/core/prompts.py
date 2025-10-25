"""Interactive prompts for ``aimem init`` (toolchain and user-scope selection).

All prompts are skippable: callers decide interactivity based on ``--no-input`` and
whether stdin is a TTY. In non-interactive mode these helpers are not called.
"""

from __future__ import annotations


def select_toolchains() -> tuple[bool, bool]:
    """Ask the user which toolchains to generate. Returns ``(kiro, copilot)``."""
    print("Which AI toolchains should aimem configure?")
    print("  [1] Both Kiro and GitHub Copilot (default)")
    print("  [2] Kiro only")
    print("  [3] GitHub Copilot only")
    while True:
        choice = input("Select 1-3 [1]: ").strip() or "1"
        if choice == "1":
            return True, True
        if choice == "2":
            return True, False
        if choice == "3":
            return False, True
        print("Please enter 1, 2, or 3.")


def confirm_user_scope() -> bool:
    """Ask whether to also set up global user memory in the home directory."""
    print()
    print("Set up global USER memory in your home directory (~/.aimem/memory/user.md)?")
    answer = input("This writes outside the project. [y/N]: ").strip().lower()
    return answer in {"y", "yes"}
