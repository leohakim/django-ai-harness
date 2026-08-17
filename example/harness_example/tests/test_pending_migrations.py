"""Guard against models that drifted away from their migrations.

A model change without a migration passes every other test and then fails on deploy, so
this belongs in the suite rather than in a pre-deploy checklist.

`makemigrations --check` verifies the migration graph against the model state and also
calls `check_consistent_history`, which opens a database connection — hence the
`django_db` mark.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_no_pending_migrations():
    try:
        call_command("makemigrations", check=True, dry_run=True, verbosity=0)
    except SystemExit as exc:  # Django exits non-zero when changes are missing.
        if exc.code not in (None, 0):
            pytest.fail(
                "Model changes are missing migrations. "
                "Run `python manage.py makemigrations` and commit the result.",
            )
