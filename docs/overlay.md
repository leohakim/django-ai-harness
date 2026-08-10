# Overlay

## Purpose

Transform a fresh **cookiecutter-django** tree into a harness-compliant project without forking upstream.

## How to run

```bash
python overlay/apply.py /path/to/project --harness-root /path/to/django-ai-harness
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
| Commands | Adds `seed_database` management command under the project package |
| Tests | Adds pending-migrations test module if missing |
| Architecture | Copies `harness_templates/app_skeleton/` reference |
| Docs | Adds `docs/django-ai-harness.md` short pointer |

## What it deliberately does **not** change

- Does not flatten `config/settings/{base,local,production,test}.py`
- Does not remove Docker/CI choices from cookiecutter
- Does not replace Ruff/pre-commit already provided upstream (extends carefully)

## Settings bridge (book ↔ cookiecutter)

*Boost Your Django DX* prefers a single settings module + env vars. cookiecutter-django uses a split. We keep the split and still apply the book’s **anti-patterns**:

- Don’t read settings at import time in random modules — use `django.conf.settings`
- Don’t mutate settings at runtime in app code
- Prefer env-driven values already via `django-environ`
- Keep custom settings well-named and tested when logic exists

See `knowledge/dx-practices/settings.md`.
