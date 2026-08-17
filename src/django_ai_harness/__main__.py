"""Allow ``python -m django_ai_harness``."""

from __future__ import annotations

from django_ai_harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
