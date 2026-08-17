#!/usr/bin/env python3
"""Compatibility entry point for ``python overlay/apply.py <project>``.

The overlay lives in :mod:`django_ai_harness.overlay` since v2.0 so that it ships in the
published wheel. This shim keeps the path documented by older generated projects working
from a plain source checkout, with no installation step.

Prefer the installed command:

    uvx django-ai-harness apply /path/to/project
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from django_ai_harness.overlay import main  # noqa: E402


def _strip_harness_root(argv: list[str]) -> list[str]:
    """Drop the v1.x ``--harness-root`` option; templates now ship inside the package."""
    cleaned: list[str] = []
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--harness-root":
            skip_next = True
            continue
        if arg.startswith("--harness-root="):
            continue
        cleaned.append(arg)
    return cleaned


if __name__ == "__main__":
    raise SystemExit(main(_strip_harness_root(sys.argv[1:])))
