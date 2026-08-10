"""Write-side business logic lives here."""

from __future__ import annotations

from django.db import transaction


@transaction.atomic
def example_create(*, name: str) -> None:
    """Replace with real domain services (keyword-only args, full_clean, etc.)."""
    raise NotImplementedError
