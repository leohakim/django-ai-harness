# cookiecutter-django defaults for agents

Upstream: `gh:cookiecutter/cookiecutter-django`.

Default pin is the single file `COOKIECUTTER_PIN` at the harness root (override with `COOKIECUTTER_DJANGO_REF`):

```text
# read from COOKIECUTTER_PIN — do not hardcode elsewhere
```

To intentionally track latest: `COOKIECUTTER_DJANGO_REF=master ./scripts/refresh-example.sh`

## Non-interactive defaults used by `scripts/new-project.sh` / `refresh-example.sh`

```text
project_name / project_slug     = caller-provided
description                     = "Project managed with django-ai-harness" (DESCRIPTION)
author_name                     = "django-ai-harness" (AUTHOR_NAME)
domain_name                     = "example.com" (DOMAIN_NAME)
open_source_license             = MIT
username_type                   = email
timezone                        = UTC
windows                         = n
editor                          = None
use_docker                      = y   # script default; USE_DOCKER=n to opt out
postgresql_version              = 16
cloud_provider                  = None
mail_service                    = Other SMTP
rest_api                        = DRF
use_async                       = n
frontend_pipeline               = None
use_celery                      = n
mail_catcher                    = None
use_sentry                      = n
use_whitenoise                  = y
use_heroku                      = n
ci_tool                         = Github
keep_local_envs_in_vcs          = n
debug                           = n
```

## Notes for agents

- After generation, **always** run the harness overlay.
- Prefer `uv run` for all Python commands.
- Do not delete `config/settings/` split.
- DRF is preferred so HackSoft API patterns apply cleanly.
- If `use_docker=n`, ensure Postgres is available or adjust DATABASE_URL per cookiecutter docs / test settings.
- Do not commit `.envs/` with real secrets; the harness default is `keep_local_envs_in_vcs=n`.
