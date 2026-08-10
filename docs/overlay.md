# Overlay

## Purpose

Transform a fresh **cookiecutter-django** tree into a harness-compliant project without forking upstream.

## How to run

```bash
python overlay/apply.py /path/to/project --harness-root /path/to/django-ai-harness
# Optional: activate PgBouncer envs (still PostgreSQL)
python overlay/apply.py /path/to/project --harness-root /path/to/django-ai-harness --with-pgbouncer
```

Properties:

- **Idempotent**: safe to run multiple times
- **Non-destructive to app domain code**: additive patches with markers
- Writes a marker file `.django-ai-harness.json` with version metadata

## What it changes

| Area | Action |
|---|---|
| Agents | Adds/updates `AGENTS.md` |
| Dependencies | Ensures DX packages in `pyproject.toml` dependency-groups.dev via `uv add --group dev` when available, else TOML edit |
| Local settings | Enables browser-reload, Rich logging hints, django-read-only, version checks |
| Commands | Adds `seed_database` under the installed `users` app (`*/users/management/commands/`) |
| Tests | Adds pending-migrations test module if missing |
| Architecture | Copies `harness_templates/app_skeleton/` reference |
| Docs | Adds `docs/django-ai-harness.md` short pointer |
| PgBouncer (opt-in) | Always installs `compose/pgbouncer/` + `docker-compose.pgbouncer.yml` and env-gated settings hooks; `--with-pgbouncer` flips `.envs` to route via the pooler |

## What it deliberately does **not** change

- Does not flatten `config/settings/{base,local,production,test}.py`
- Does not remove Docker/CI choices from cookiecutter
- Does not replace Ruff/pre-commit already provided upstream (extends carefully)
- Does not change the database engine away from PostgreSQL

## PgBouncer

Keep Postgres; reduce connection RAM on small/medium hosts:

```bash
python overlay/apply.py /path/to/project --harness-root . --with-pgbouncer
# or: WITH_PGBOUNCER=1 ./scripts/new-project.sh ~/Projects/my_app
```

See `knowledge/dx-practices/postgres-pooling.md` and `compose/pgbouncer/README.md` in generated projects.

## Settings bridge (book ↔ cookiecutter)

*Boost Your Django DX* prefers a single settings module + env vars. cookiecutter-django uses a split. We keep the split and still apply the book’s **anti-patterns**:

- Don’t read settings at import time in random modules — use `django.conf.settings`
- Don’t mutate settings at runtime in app code
- Prefer env-driven values already via `django-environ`
- Keep custom settings well-named and tested when logic exists

See `knowledge/dx-practices/settings.md`.
