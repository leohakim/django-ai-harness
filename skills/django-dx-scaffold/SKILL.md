---
name: django-dx-scaffold
description: Scaffold a new Django project using cookiecutter-django latest plus the django-ai-harness overlay. Use when the user wants a new Django app, greenfield project, or harness bootstrap.
---

# django-dx-scaffold

## Goal

Create a new Django project that is **cookiecutter-django (pinned ref) + django-ai-harness overlay**.

## Prerequisites

Confirm `uv` and `cookiecutter` are installed. If missing, help the user install them.

## Steps

1. Locate the django-ai-harness checkout (this skill’s repo root two levels up from `skills/django-dx-scaffold`, or ask the user for the path).
2. Ask for target directory and project display name if not provided.
3. Prefer the guided TUI for humans (`./scripts/new-project-tui.sh`). For automation, run:

```bash
./scripts/new-project.sh <target_directory> "<Project Name>"

# with PgBouncer + Docker
WITH_PGBOUNCER=1 ./scripts/new-project.sh <target_directory> "<Project Name>"
```

5. `cd` into the project and run:
   - `uv sync`
   - `uv run python manage.py check` (with required `POSTGRES_*` env / Compose up)
6. Summarize for the user:
   - path created
   - how to migrate / runserver
   - if PgBouncer: point to `knowledge/dx-practices/postgres-pooling.md` and migrate via direct Postgres
   - remind HackSoft rules (`django-hacksoft` skill)

## Rules

- Do **not** invent an alternate project layout.
- Do **not** skip the overlay.
- Do **not** copy copyrighted book text into the project.
- Prefer DRF + harness defaults unless the user overrides.
- PgBouncer is opt-in only; default stays plain PostgreSQL.
- Do **not** switch the database engine away from PostgreSQL when enabling pooling.

## Verification

- `manage.py` exists
- `.django-ai-harness.json` exists
- `AGENTS.md` exists
- `harness_templates/app_skeleton/` exists
