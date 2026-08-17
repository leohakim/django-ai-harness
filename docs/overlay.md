# The overlay

## Purpose

Turn a fresh cookiecutter-django tree into a harness-compliant project without forking
upstream. Everything the harness adds is a diff you can read, applied by
`src/django_ai_harness/overlay.py`.

## Running it

```bash
uvx django-ai-harness apply /path/to/project
uvx django-ai-harness apply /path/to/project --with-pgbouncer
uvx django-ai-harness apply /path/to/project --check   # report drift, write nothing
uvx django-ai-harness apply /path/to/project --force   # overwrite files you edited
```

From a source checkout, `python overlay/apply.py /path/to/project` still works.

## The three guarantees

### Idempotent

Running it twice produces the same tree. Settings patches live inside uniquely named
marker blocks:

```python
# >>> django-ai-harness:local
...
# <<< django-ai-harness:local
```

Blocks are matched with line anchors, so `:local` can never match the end of
`:pgbouncer`. Bare `# >>> django-ai-harness` markers written by version 1.x are migrated
to their namespaced form on the first run.

### Hermetic

No network access, no dependency resolver, no subprocess. The DX dependencies are pinned
with `==` in `src/django_ai_harness/data/dev-requirements.txt` and merged directly into
`[dependency-groups].dev`, sorted by project name so the result is stable.

This is deliberate. Version 1.x ran `uv add --group dev`, which resolved against PyPI at
apply time and wrote `>=` pins — so regenerating the golden example produced a different
tree depending on the day, and CI would eventually fail on every open pull request for
reasons unrelated to the change.

### Upgrade-aware

`.django-ai-harness.json` records the SHA-256 of the content the overlay last wrote for
each file it owns:

```json
{
  "harness": "django-ai-harness",
  "overlay_version": "2.0.0",
  "features": { "pgbouncer": false },
  "managed_files": { "AGENTS.md": "…" }
}
```

| File state | Action | Reported as |
|---|---|---|
| missing | write it | `created` |
| identical to the new content | nothing | `unchanged` |
| identical to what the overlay last wrote | write the new content | `updated` |
| differs from both | leave it alone | `skipped (local edits)` |
| exists but was never recorded | leave it alone | `skipped (pre-existing file)` |

That last row matters: the overlay never adopts a file it did not create. The state file
carries no timestamps, so it stays byte-stable and the golden example does not churn.

Edits *inside* a marker block (`# >>> django-ai-harness:local`, `:base`, `:pgbouncer`,
`:urls`) are overlay territory: the next `apply` replaces the block in place, with no
skip and no `--force`. Whole-file ownership is hashed; blocks are not. Put project-local
additions *outside* the markers.

### `--check`

`--check` is dry-run plus an exit code:

| Situation | Exit |
|---|---|
| Overlay would create or update a file | 1 |
| 1.x upgrade still pending (`skipped (untracked, pre-2.0)`) | 1 |
| Only locally edited managed files (`skipped (local edits)`) | 0 |
| Tree already matches | 0 |

## What it changes

| Target | Change |
|---|---|
| `pyproject.toml` | Merges the pinned DX dependencies into `[dependency-groups].dev` |
| `config/settings/base.py` | Settings hygiene notes; registers `django_linear_migrations` and `django_version_checks` behind an `ImportError` guard; sets `VERSION_CHECKS` from the project's `.python-version` |
| `config/settings/local.py` | `django_browser_reload`, `django_read_only`, `django_rich`, `SHELL_PLUS`, Rich console handler |
| `config/settings/local.py`, `production.py` | Inert `USE_PGBOUNCER` block |
| `config/urls.py` | Browser-reload URLs behind `DEBUG`, guarded by `ImportError` |
| `AGENTS.md` | The architecture and DX contract |
| `skills/django-hacksoft/`, `skills/django-dx-review/` | Agent Skills that travel with the project |
| `<package>/users/management/commands/seed_database.py` | Factory Boy seeding command |
| `<package>/tests/test_pending_migrations.py` | Fails when models drifted from migrations |
| `harness_templates/app_skeleton/` | Reference services, selectors and thin APIs |
| `*/migrations/max_migration.txt` | Tracks the latest migration for `django-linear-migrations` |
| `compose/pgbouncer/`, `docker-compose.pgbouncer.yml` | Opt-in pooling assets |
| `docker-compose.pgbouncer.production.yml` | Production `env_file` override |
| `docs/django-ai-harness.md` | How to upgrade |

### Why system checks live in base settings

`django-linear-migrations` and `django-version-checks` register Django *system checks*.
`config/settings/test.py` imports from `base`, not `local`, so a check registered only in
local settings never runs during tests — which is exactly when a migration conflict
should be caught. They therefore go in base, guarded by `ImportError` so a production
image that ran `uv sync --no-dev` still boots. Purely interactive tooling
(browser-reload, read-only, Rich) stays local.

### Why the Rich handler is patched, not assigned

The overlay writes:

```python
LOGGING["handlers"]["console"] = { ... "class": "rich.logging.RichHandler" ... }
```

rather than a fresh `LOGGING = {...}`. Assigning a new dictionary would silently discard
cookiecutter-django's formatters and loggers.

## What it deliberately does not change

- It does not flatten the settings split into a single module.
- It does not remove Docker, CI or cloud choices made at generation time.
- It does not replace the Ruff or pre-commit configuration cookiecutter-django ships.
- It does not change the database engine away from PostgreSQL.
- It does not touch files it did not create.

## Settings hygiene

*Boost Your Django DX* prefers a single settings module driven by environment variables;
cookiecutter-django uses a split. The harness keeps the split and applies the underlying
anti-patterns within it:

- Import `django.conf.settings` from application code, never a settings module directly.
- Never mutate settings at runtime from request or business code.
- Keep environment-specific values in environment variables.
- Name custom settings well, and test them when they carry logic.

See [knowledge/dx-practices/settings.md](../knowledge/dx-practices/settings.md).

## Extending it

Add a step as a method on `Overlay` and call it from `apply()`. Use `write_managed` for
files the harness should be able to upgrade later, `upsert_block` for patches inside
existing files, and `write_if_missing` only for structural files such as `__init__.py`.
Then add a test in `tests/test_overlay.py` and run `./scripts/refresh-example.sh`.
