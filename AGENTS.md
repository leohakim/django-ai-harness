# AGENTS.md — django-ai-harness (meta-repository)

This repository is the harness itself, not a Django application. It generates and
maintains Django projects. If you are working *inside* a generated project, read that
project's own `AGENTS.md` instead.

## What this repository is

1. A CLI (`src/django_ai_harness/`) that generates cookiecutter-django at a pinned commit
   and applies an idempotent overlay on top.
2. A knowledge base (`knowledge/`) explaining why each practice exists.
3. Portable Agent Skills (`skills/`) that enforce those practices in user projects.
4. A golden `example/` that CI regenerates to catch upstream drift.

## Read first

- `README.md`
- `docs/for-agents.md`
- `knowledge/architecture/hacksoft.md`
- `src/django_ai_harness/overlay.py` — the module docstring states the design contract

## Hard rules

**Never break these three properties of the overlay.** Each is covered by tests in
`tests/test_overlay.py`; if you change behaviour, the tests must still express the
property.

- **Idempotent** — applying twice produces the same tree.
- **Hermetic** — no network access, no dependency resolver, no subprocess. DX
  dependencies come from `data/dev-requirements.txt`, pinned with `==`. Loosening those
  pins to `>=` makes regeneration non-reproducible and breaks CI for every contributor.
- **Upgrade-aware** — a file the user edited is reported, never overwritten without
  `--force`.

Additionally:

- Never commit copyrighted book text, PDFs, or long excerpts.
- Keep cookiecutter-django's settings split (`config/settings/{base,local,production,test}.py`).
  Apply the book's anti-patterns *inside* that split rather than flattening it.
- Register system checks in **base** settings; they must run under
  `config.settings.test`. Local-only tooling goes in **local**.
- Marker block names must never be a prefix of another marker name.
- PgBouncer stays opt-in and PostgreSQL stays the engine.
- When overlay behaviour changes: run `./scripts/refresh-example.sh`, commit `example/`,
  and add a `CHANGELOG.md` entry.

## Working here

```bash
uv sync --extra wizard
uv run pytest                       # the suite must stay green
uv run ruff check . && uv run ruff format --check .
./scripts/refresh-example.sh        # after any overlay change
```

The version lives in `pyproject.toml` and `src/django_ai_harness/__init__.py`.
`tests/test_repo.py` fails if they disagree or if `CHANGELOG.md` lacks an entry.

## Skills

- `django-dx-scaffold` — create a new project
- `django-hacksoft` — implement and review domain code
- `django-dx-review` — audit a project before a pull request
