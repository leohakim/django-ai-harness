import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_no_pending_migrations():
    """Fail if model changes are missing migrations."""
    try:
        call_command("makemigrations", check=True, dry_run=True)
    except SystemExit as exc:  # Django may exit non-zero
        if exc.code not in (None, 0):
            raise AssertionError("Pending migrations detected") from exc
