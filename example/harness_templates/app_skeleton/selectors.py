"""Read-side queries.

Selectors answer questions. They may return querysets, iterables, objects, ids or
shaped data, and they never mutate state.
"""

from __future__ import annotations

from django.db.models import QuerySet


def example_list() -> QuerySet:
    """Replace with a real domain selector."""
    raise NotImplementedError
