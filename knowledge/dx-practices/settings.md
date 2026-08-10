# Settings practices

## Keep cookiecutter’s split

Use `config/settings/base.py`, `local.py`, `production.py`, `test.py`.

## Anti-patterns to avoid (still apply)

1. **Don’t import your project settings module** from app code — use `from django.conf import settings`.
2. **Don’t mutate settings** at runtime in requests/commands (except documented test overrides).
3. **Don’t hide business logic** in settings callables that hit the database at import time.
4. **Prefer env vars** via `django-environ` already wired by cookiecutter-django.
5. **Name custom settings** clearly (`MYPROJECT_*`) and document them near definition.
6. **Override complex settings carefully** in `local.py`/`production.py` (extend lists instead of silently replacing when possible).

## Local DX toggles

Local settings may enable debug toolbar, browser-reload, extensions, and read-only shell helpers. Keep those out of production settings.

## PgBouncer (opt-in)

When `USE_PGBOUNCER=True`, overlay hooks set `CONN_MAX_AGE=0` and `DISABLE_SERVER_SIDE_CURSORS=True` for transaction pooling. See `knowledge/dx-practices/postgres-pooling.md`.
