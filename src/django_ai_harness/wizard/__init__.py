"""Guided Textual TUI for creating a django-ai-harness project."""

from __future__ import annotations

__all__ = ["run"]


def run(*, language: str = "en", target=None) -> int:
    """Launch the wizard. Imported lazily so Textual stays an optional dependency."""
    from django_ai_harness.wizard.app import run as _run  # noqa: PLC0415

    return _run(language=language, target=target)
