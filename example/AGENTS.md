# AGENTS.md

Bootstrapped with [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django)
and [django-ai-harness](https://github.com/leohakim/django-ai-harness).

This file is the contract every agent working in this repository follows. It is owned by
the harness overlay: edit it freely, but be aware that a locally edited copy stops
receiving harness upgrades until you re-run the overlay with `--force`.

## Architecture — HackSoft Django Styleguide

| Concern | Home |
|---|---|
| Writes, workflows, side effects | `services.py` / `services/` |
| Reads, filtering, visibility | `selectors.py` / `selectors/` |
| HTTP input & output | thin APIs calling services and selectors |
| Simple non-relational invariants | `Model.clean` or database constraints |

Business rules never live in views, serializers, forms, signals, `Model.save`, custom
managers or querysets. See `harness_templates/app_skeleton/` for the reference layout.

`users/` is cookiecutter-django's allauth app. Do not copy its views, serializers or
templates as the pattern for new domain code — copy `harness_templates/app_skeleton/`
instead.

- Services take keyword-only arguments, call `full_clean()` before saving, and wrap
  multi-step writes in `transaction.atomic`.
- Selectors never mutate state.
- Side effects that depend on committed rows run in `transaction.on_commit`.
- Tests mirror the layers: `tests/services/`, `tests/selectors/`, `tests/apis/`.

## Developer experience

- Run everything through `uv run`; the lockfile is the source of truth.
- Keep Ruff and pre-commit green before proposing a change.
- Seed local data with `python manage.py seed_database` plus Factory Boy factories.
- Migrations are linear: `django-linear-migrations` maintains `max_migration.txt`.
  Resolve conflicts with `python manage.py rebase_migration <app>`.
- `django-read-only` is available for safe shell sessions:
  `import django_read_only; django_read_only.enable()`.

## Harness

- State lives in `.django-ai-harness.json`. Do not hand-edit it.
- Upgrade with `django-ai-harness apply .` (add `--check` in CI to detect drift).
- Optional PostgreSQL connection pooling lives in `compose/pgbouncer/`.

## Skills

This project ships `skills/django-hacksoft` and `skills/django-dx-review`. Use them for
feature work and before opening a pull request. They travel with the overlay; do not
wait for a copy from the harness repository.
