# Practices changelog

## 2026-08-10 — harness v1.1

- Opt-in **PgBouncer** templates + env-gated settings (`WITH_PGBOUNCER=1` / `--with-pgbouncer`)
- `WITH_PGBOUNCER=1` forces `USE_DOCKER=y` so Compose postgres exists
- `seed_database` lives under the installed `users` app (command discovery)

## 2026-08-10 — harness v1

- Bootstrap via cookiecutter-django pinned ref + idempotent overlay
- Map classic DX book themes to `uv` + Ruff
- Add browser-reload, django-rich, django-read-only, linear-migrations, version-checks, seed command
- Enforce HackSoft services/selectors via skills + templates
- Public MIT open-source repo with agent docs
