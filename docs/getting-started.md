# Getting started

## Requirements

- [uv](https://docs.astral.sh/uv/) — everything else is fetched on demand
- Git
- **Docker**, unless you pass `--use-docker n`

The harness runs on Python 3.11 or newer. The project it generates targets the Python
version of the pinned cookiecutter-django, currently 3.14; `uv` installs that for you.

> **Docker is needed to *generate* the project, not only to run it.**
> cookiecutter-django's post-generation hook fills in `pyproject.toml` by running `uv`
> inside a container it builds for the purpose. That happens whenever `use_docker=y`,
> which is the default. With `--use-docker n` the hook runs `uv` on your machine and
> Docker is not involved at all.

## Create a project

```bash
uvx django-ai-harness new ~/Projects/my_shop "My Shop"
```

The first argument is the directory to create — its name becomes the Python package, so
`my_shop` becomes `my_shop`, and `my-shop` is normalised to `my_shop`. The second is the
human-readable name.

Then:

```bash
cd ~/Projects/my_shop
uv sync
docker compose -f docker-compose.local.yml up -d
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Visit http://127.0.0.1:8000.

### Without Docker

```bash
uvx django-ai-harness new ~/Projects/my_shop "My Shop" --use-docker n
```

Provide the database yourself before migrating:

```bash
export DATABASE_URL=postgres://user:password@localhost:5432/my_shop
uv run python manage.py migrate
```

### Guided wizard

```bash
uvx --from 'django-ai-harness[wizard]' django-ai-harness wizard
```

Each screen explains what a choice **adds**, what it **leaves out**, and the practical
implication. Use `--lang es` for Spanish, or let it follow your `LANG`.

## Available options

Everything the wizard asks is a flag on `new`:

| Flag | Values | Default |
|---|---|---|
| `--use-docker` | `y`, `n` | `y` |
| `--rest-api` | `DRF`, `Django Ninja`, `None` | `DRF` |
| `--use-celery` | `y`, `n` | `n` |
| `--frontend-pipeline` | `None`, `Webpack`, `Gulp`, `Django Compressor` | `None` |
| `--ci-tool` | `Github`, `Gitlab`, `None` | `Github` |
| `--use-whitenoise` | `y`, `n` | `y` |
| `--use-sentry` | `y`, `n` | `n` |
| `--cloud-provider` | `None`, `AWS`, `GCP`, `Azure` | `None` |
| `--with-pgbouncer` | flag | off (implies `--use-docker y`) |
| `--slug` | Python package name | derived from the target directory |
| `--author-name`, `--email`, `--domain-name`, `--description`, `--timezone` | free text | sensible defaults |

Run `uvx django-ai-harness new --help` for the full list.

## What you get

Beyond a standard cookiecutter-django project:

```text
my_shop/
├── AGENTS.md                        architecture and DX contract for agents
├── .django-ai-harness.json          overlay version and managed-file state
├── harness_templates/app_skeleton/  reference services / selectors / APIs
├── compose/pgbouncer/               opt-in connection pooling
├── docs/django-ai-harness.md        how to upgrade the harness
└── my_shop/
    ├── users/management/commands/seed_database.py
    └── tests/test_pending_migrations.py
```

Plus, inside the settings split:

- **base** — settings hygiene notes, `django-linear-migrations` and
  `django-version-checks` (registered here so their system checks also run under
  `config.settings.test`, and therefore in CI)
- **local** — `django-browser-reload`, `django-read-only`, Rich console logging,
  IPython `shell_plus`
- **local and production** — an inert `USE_PGBOUNCER` block, active only if you opt in

## First steps in a new project

```bash
uv run pre-commit install          # the hooks cookiecutter-django ships
uv run python manage.py seed_database
uv run pytest
```

Write a first app following `harness_templates/app_skeleton/`: business writes go in
`services.py`, reads in `selectors.py`, and the HTTP layer stays thin.

## Keeping the harness up to date

```bash
uvx django-ai-harness apply .
uv sync
uv run python manage.py check
```

Add `--check` to your project's CI to fail the build when it drifts behind the harness:

```yaml
- run: uvx django-ai-harness apply . --check
```

See [updating.md](updating.md) for the details of what gets updated and what does not.

## Troubleshooting

**`target already exists`** — `new` never writes into an existing directory. Choose
another path or remove it.

**`'2fast' is not a usable Python package name`** — the directory name must be a valid
Python identifier. Pass `--slug` explicitly.

**Migrations hang with PgBouncer enabled** — DDL must bypass the pooler:
`python manage.py migrate --database=direct`. See
[knowledge/dx-practices/postgres-pooling.md](../knowledge/dx-practices/postgres-pooling.md).

**`apply` reports "skipped (local edits)"** — you edited a file the overlay owns, so it
was preserved. Review the upstream version, then re-run with `--force` if you want the
harness copy back.

**`Error installing local dependencies: ... exit status 137`** — cookiecutter-django's
post-generation hook runs `uv` in a container, and that container was killed, almost
always for running out of memory. Retry; if it keeps happening, raise Docker's memory
limit, or generate with `--use-docker n`, which skips the container entirely. This is
upstream behaviour, not something the harness controls — see
[maintaining.md](maintaining.md).

**`docker: command not found` during generation** — same cause. Either start Docker or
pass `--use-docker n`.
