# AGENTS.md

This project was bootstrapped with **cookiecutter-django** and **django-ai-harness**.

## Architecture (HackSoft)

- Business writes/workflows → `services.py` (or `services/`)
- Business reads/queries → `selectors.py` (or `selectors/`)
- HTTP layer stays thin (DRF APIs / views call services & selectors)
- Do not put domain rules in serializers, signals, or `Model.save`

See harness knowledge: `knowledge/architecture/hacksoft.md` in the django-ai-harness repo.

## DX

- Use `uv run` for commands
- Keep Ruff + pre-commit green
- Prefer `seed_database` + Factory Boy for local data
- Re-apply overlay after harness upgrades
- Optional low-RAM Postgres path: PgBouncer templates in `compose/pgbouncer/` (see harness `knowledge/dx-practices/postgres-pooling.md`)

## Skills

If Cursor skills from django-ai-harness are available, use:

- `django-hacksoft` for feature work
- `django-dx-review` before PRs
