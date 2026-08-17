"""django-ai-harness: opinionated Django bootstrap for humans and AI agents.

The package exposes three building blocks:

* :mod:`django_ai_harness.pins` — the pinned upstream refs the harness is built on.
* :mod:`django_ai_harness.overlay` — the idempotent overlay applied to a generated project.
* :mod:`django_ai_harness.scaffold` — cookiecutter-django generation + overlay in one call.
"""

from __future__ import annotations

__all__ = ["OVERLAY_VERSION", "__version__"]

#: Distribution version (kept in sync with ``pyproject.toml`` by ``tests/test_repo.py``).
__version__ = "2.0.0"

#: Overlay contract version written into ``.django-ai-harness.json`` of generated projects.
OVERLAY_VERSION = "2.0.0"
