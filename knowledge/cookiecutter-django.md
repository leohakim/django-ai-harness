# cookiecutter-django defaults

Upstream: [`cookiecutter/cookiecutter-django`](https://github.com/cookiecutter/cookiecutter-django).

The harness generates from an **exact commit**, never a branch. The pin lives in one
place:

```text
src/django_ai_harness/data/cookiecutter-django.pin
```

Override it for a single run with the `COOKIECUTTER_DJANGO_REF` environment variable.
That is how the scheduled drift job probes upstream tip:

```bash
COOKIECUTTER_DJANGO_REF=master ./scripts/refresh-example.sh
```

Inspect the current pin with `django-ai-harness info`.

## Context used by the harness

`django-ai-harness new` drives cookiecutter through its Python API with this context.
Everything marked *flag* is exposed on the command line and in the wizard.

| Key | Value | Flag |
|---|---|---|
| `project_name` | caller-provided | positional |
| `project_slug` | derived from the target directory | `--slug` |
| `description` | `Project managed with django-ai-harness` | `--description` |
| `author_name` | `django-ai-harness` | `--author-name` |
| `domain_name` | `example.com` | `--domain-name` |
| `email` | `hello@<domain>` | `--email` |
| `timezone` | `UTC` | `--timezone` |
| `use_docker` | `y` | `--use-docker` |
| `rest_api` | `DRF` | `--rest-api` |
| `use_celery` | `n` | `--use-celery` |
| `frontend_pipeline` | `None` | `--frontend-pipeline` |
| `ci_tool` | `Github` | `--ci-tool` |
| `use_whitenoise` | `y` | `--use-whitenoise` |
| `use_sentry` | `n` | `--use-sentry` |
| `cloud_provider` | `None` | `--cloud-provider` |
| `open_source_license` | `MIT` | — |
| `username_type` | `email` | — |
| `postgresql_version` | `16` | — |
| `mail_service` | `Other SMTP` | — |
| `use_async`, `use_heroku`, `windows`, `debug` | `n` | — |
| `editor`, `mail_catcher` | `None` | — |
| `keep_local_envs_in_vcs` | `n` | — |

`keep_local_envs_in_vcs=n` is not negotiable: it keeps `.envs/` out of version control.

The context is passed as a dictionary, so values containing `=` or spaces need no
escaping. Only control characters are rejected.

## Notes for agents

- After generation, **always** apply the harness overlay. `new` does this for you.
- Prefer `uv run` for every Python command in a generated project.
- Never flatten the `config/settings/` split.
- DRF is the default because the HackSoft API patterns and the shipped app skeleton
  assume it.
- With `use_docker=n`, provide `DATABASE_URL` or the `POSTGRES_*` variables before
  migrating.
- Never commit `.envs/` with real secrets.
