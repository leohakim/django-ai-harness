# django-ai-harness

This project carries the [django-ai-harness](https://github.com/leohakim/django-ai-harness)
overlay: a set of developer-experience defaults and an architecture contract shared by
humans and AI agents.

## Upgrading the harness

```bash
uvx django-ai-harness apply .          # or: uv run django-ai-harness apply .
uv sync
uv run python manage.py check
```

The overlay is idempotent and tracks the files it owns in `.django-ai-harness.json`.
Files you edited locally are never overwritten; they are reported instead, and
`--force` overrides that protection once you have reviewed the diff.

`--check` exits 1 when the overlay would write files, or when a 1.x upgrade is still
pending. Locally edited managed files are listed and do **not** fail `--check`.

## Where things live

| Path | Purpose |
|---|---|
| `AGENTS.md` | Architecture and DX contract for agents and humans |
| `skills/django-hacksoft/` | Agent Skill that enforces services / selectors / thin APIs |
| `skills/django-dx-review/` | Agent Skill for a defect-first review before a pull request |
| `harness_templates/app_skeleton/` | Reference services / selectors / API layout |
| `compose/pgbouncer/` | Opt-in PostgreSQL connection pooling |
| `.django-ai-harness.json` | Overlay version and managed-file state |

## Connection pooling

PgBouncer is opt-in and keeps PostgreSQL as the engine. Enable it with
`django-ai-harness apply . --with-pgbouncer` and read `compose/pgbouncer/README.md`.
