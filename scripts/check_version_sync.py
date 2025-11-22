#!/usr/bin/env python3
"""Fail if package.json and aimem.__version__ disagree.

Both the Python package and the npm launcher are published from this repository, so their
versions must stay in lockstep. Run as part of CI.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def python_version() -> str:
    text = (ROOT / "src" / "aimem" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        raise SystemExit("could not find __version__ in src/aimem/__init__.py")
    return match.group(1)


def npm_version() -> str:
    data = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    return str(data["version"])


def main() -> int:
    py = python_version()
    npm = npm_version()
    if py != npm:
        print(f"version mismatch: aimem.__version__={py!r} but package.json={npm!r}")
        return 1
    print(f"versions match: {py}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
