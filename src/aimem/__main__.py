"""Executable entry point for ``python -m aimem``."""

from __future__ import annotations

import sys

from aimem.cli import main

if __name__ == "__main__":
    sys.exit(main())
