---
name: django-dx-scaffold
description: Scaffold a new Django project using cookiecutter-django at a pinned commit plus the django-ai-harness overlay, or upgrade the harness inside an existing project. Use when the user wants a new Django app, a greenfield project, a harness bootstrap, or wants to bring an existing harness project up to date.
---

# django-dx-scaffold

## Goal

Create a Django project that is **cookiecutter-django at a pinned commit + the
django-ai-harness overlay**, or upgrade the overlay in a project that already has it.

## Prerequisites

`uv` must be installed. Everything else is fetched on demand — there is nothing to clone
and no separate cookiecutter install.

If `uv` is missing, point the user at https://docs.astral.sh/uv/ and stop.

## Creating a project

1. Ask for the target directory and the human-readable project name if they were not
   given. The directory name becomes the Python package, so it must be a valid
   identifier; `my-shop` is normalised to `my_shop`.
2. Run:

```bash
uvx django-ai-harness new <target_directory> "<Project Name>"
```

3. Express the user's choices as **flags**, never by editing generated files afterwards:

| Want | Flag |
|---|---|
| Background jobs | `--use-celery y` |
| No containers | `--use-docker n` |
| Typed API | `--rest-api "Django Ninja"` |
| No API framework | `--rest-api None` |
| Connection pooling | `--with-pgbouncer` (implies Docker) |
| Cloud media storage | `--cloud-provider AWS\|GCP\|Azure` |
| Error tracking | `--use-sentry y` |
| Asset bundling | `--frontend-pipeline Webpack` |

Run `uvx django-ai-harness new --help` when unsure. Do not guess a flag name.

4. Report the pinned commit if the user asks what they are getting:
   `uvx django-ai-harness info`. Only set `COOKIECUTTER_DJANGO_REF` when the user
   explicitly wants to drift from the pin.

## Upgrading an existing project

```bash
uvx django-ai-harness apply .
uvx django-ai-harness apply . --check   # report drift only, exit 1 if stale
```

Read the output carefully:

- `skipped (local edits)` — the user edited a file the overlay owns. **Surface this to
  the user and let them decide.** Never pass `--force` on your own initiative; it
  discards their work.
- `skipped (pre-existing file)` — the file was there before the overlay and is not
  managed. This is normal.

## Verification

After either operation:

```bash
test -f <target>/AGENTS.md
test -f <target>/.django-ai-harness.json
test -d <target>/harness_templates/app_skeleton
uvx django-ai-harness apply <target> --check    # must exit 0
```

Then, inside the project:

```bash
uv sync
uv run python manage.py check
```

`manage.py check` needs database settings. With Docker, bring Compose up first; without
it, export `DATABASE_URL`.

## Rules

- Do not invent an alternative project layout; the template already provides one.
- Do not skip the overlay.
- Do not flatten the `config/settings/` split.
- Do not copy copyrighted book text into the project.
- PgBouncer is opt-in; the default stays direct PostgreSQL.
- Never switch the database engine away from PostgreSQL when enabling pooling.

## Handing off

Summarise for the user:

- the path created and the package name
- how to migrate and run the server (the command prints this)
- with PgBouncer: migrations go through `manage.py migrate --database=direct`
- that architecture rules live in the project's `AGENTS.md`, and that the
  `django-hacksoft` skill enforces them during feature work
