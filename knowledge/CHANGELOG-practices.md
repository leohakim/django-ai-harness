# Practices changelog

## 2026-08-10 — harness v1.2.0

- Guided **Textual TUI** wizard (`./scripts/new-project-tui.sh`) with Spanish UI + English technical labels
- Shared `scripts/lib/scaffold.py` used by TUI and non-interactive CLI

## 2026-08-10 — harness v1.1.1

- Default `USE_DOCKER=y` so quickstart migrate path works with Compose
- Scaffold files (`AGENTS.md`, seed, skeleton) created only if missing
- Wire Rich console logging in local settings
- CI asserts `seed_database`; upstream workflow tracks cookiecutter `master`

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
