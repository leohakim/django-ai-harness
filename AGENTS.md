# AGENTS.md — django-ai-harness (meta-repo)

This repository is an open-source **knowledge + overlay harness** for Django projects.

## Mission

1. Bootstrap new Django apps from **cookiecutter-django (latest)** + this repo’s **overlay**.
2. Enforce **HackSoft-style** services/selectors architecture.
3. Encode modern DX practices inspired by *Boost Your Django DX* (without copying the book).

## Read first

- `README.md`
- `docs/for-agents.md`
- `knowledge/book-map.md`
- `knowledge/architecture/hacksoft.md`
- `overlay/README.md`

## Hard rules

- Never commit or paste copyrighted book PDFs/long excerpts.
- Prefer idempotent overlay changes over one-off manual edits.
- Keep cookiecutter-django’s settings split (`config/settings/*`); apply book anti-patterns *inside* that split.
- Business logic belongs in services/selectors, not views/serializers/signals/`save()`.
- When changing overlay behavior, refresh `example/` and update docs.
- PgBouncer is **opt-in** (`--with-pgbouncer` / `WITH_PGBOUNCER=1`); default stays plain PostgreSQL.

## Skills

Use skills under `skills/`:

- `django-dx-scaffold` — create a new project
- `django-hacksoft` — implement/review domain code
- `django-dx-review` — audit DX/compliance
