# Getting started — project from zero

This guide walks you from an empty machine to a running Django app created with **django-ai-harness**.

## 0. Prerequisites

Install:

```bash
# macOS example
brew install uv git
# cookiecutter (pick one)
brew install cookiecutter
# or: uv tool install cookiecutter
```

Verify:

```bash
uv --version
cookiecutter --version
git --version
```

## 1. Get the harness

```bash
git clone https://github.com/leohakim/django-ai-harness.git
cd django-ai-harness
```

You can keep this clone permanently: it is your source of practices, overlay, and skills.

## 2. Create the project

### Option A — script (recommended)

```bash
./scripts/new-project.sh ~/Projects/my_shop
```

> The directory basename becomes the Python package slug. Prefer underscores
> (`my_shop`) over hyphens (`my-shop`); the script sanitizes hyphens to underscores
> when needed, but the target path is kept as you passed it.

The script will:

1. Run `cookiecutter` against **`gh:cookiecutter/cookiecutter-django`** (latest `master`).
2. Apply the **overlay** from this repo (`overlay/apply.py`).
3. Print next commands.

### Option B — Cursor agent

Open this repo in Cursor and ask:

> Use the `django-dx-scaffold` skill to create a new Django project at `~/Projects/my_shop`.

### Option C — manual two-step

```bash
cookiecutter gh:cookiecutter/cookiecutter-django
# answer prompts, then:
python overlay/apply.py /path/to/generated/project --harness-root .
```

## 3. Recommended cookiecutter answers

See [../knowledge/cookiecutter-django.md](../knowledge/cookiecutter-django.md) for the full matrix.

Sensible defaults for API + DX (what `new-project.sh` uses in non-interactive mode / what we recommend):

| Prompt | Suggested |
|---|---|
| `use_docker` | `y` if you want Postgres/Redis via Compose; `n` for simplest local SQLite-less path (still needs Postgres typically) |
| `rest_api` | `DRF` (HackSoft APIs fit well) |
| `ci_tool` | `Github` |
| `use_celery` | `n` until you need it |
| `cloud_provider` | `None` until you deploy |
| `frontend_pipeline` | `None` unless you need Webpack/Gulp |
| `open_source_license` | `MIT` |

> cookiecutter-django expects **PostgreSQL** for real runs. Use Docker Compose from the generated project, or point `DATABASE_URL` at a local Postgres.

## 4. Install dependencies and run

```bash
cd ~/Projects/my_shop
uv sync
# If Docker was enabled:
# docker compose -f docker-compose.local.yml up -d
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open the site (usually `http://127.0.0.1:8000/`). With the overlay, template/static changes can auto-reload via **django-browser-reload** when configured in local settings.

## 5. Seed development data

```bash
uv run python manage.py seed_database
```

Customize the command (and Factory Boy factories) as your models grow.

## 6. Create your first domain app (HackSoft)

```bash
uv run python manage.py startapp catalog
# Move into the project package if cookiecutter uses a nested layout, e.g.:
# mv catalog my_shop/
```

Then shape the app like this:

```text
catalog/
├── models.py
├── services.py      # writes / workflows
├── selectors.py     # reads / queries
├── apis/            # thin DRF endpoints
│   └── ...
└── tests/
    ├── services/
    ├── selectors/
    └── apis/
```

Rules of thumb:

- **Services** mutate state (`transaction.atomic`, `full_clean()`).
- **Selectors** only read.
- **APIs** validate input, call services/selectors, serialize output.

Use the `django-hacksoft` skill while implementing.

The overlay also drops `harness_templates/app_skeleton/` into the project as a copy-paste reference.

## 7. Quality gates

```bash
uv run ruff check .
uv run ruff format .
uv run pre-commit run --all-files
uv run pytest
uv run python manage.py check
```

## 8. Done checklist

- [ ] Project created via cookiecutter-django latest + overlay
- [ ] `uv sync` succeeds
- [ ] Migrations applied; superuser created
- [ ] `AGENTS.md` present in the project
- [ ] First domain logic lives in services/selectors
- [ ] Pre-commit installed: `uv run pre-commit install`
- [ ] You know how to re-apply overlay later (`python /path/to/django-ai-harness/overlay/apply.py .`)

## Next reading

- [benefits.md](benefits.md) — why this setup pays off
- [overlay.md](overlay.md) — exact changes
- [for-agents.md](for-agents.md) — agent contract
- [updating.md](updating.md) — keep practices fresh
