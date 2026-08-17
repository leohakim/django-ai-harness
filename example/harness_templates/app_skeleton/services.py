"""Write-side business logic.

Services own workflows and side effects. They take keyword-only arguments, validate
with `full_clean()` before saving, and wrap multi-step writes in a transaction.
"""

from __future__ import annotations

from django.db import transaction


@transaction.atomic
def example_create(*, name: str) -> None:
    """Replace with a real domain service."""
    raise NotImplementedError
