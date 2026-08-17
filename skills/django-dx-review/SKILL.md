---
name: django-dx-review
description: Audit a Django project for django-ai-harness developer-experience and HackSoft architecture compliance. Use before opening a pull request, after scaffolding, or whenever asked to review a Django project's structure, settings, migrations, dependencies, or layering.
---

# django-dx-review

## Goal

Produce a defect-first review. Lead with what is wrong and why it matters; do not open
with a summary of what the project does.

## Gather evidence first

Run what you can before judging anything:

```bash
uvx django-ai-harness apply . --check    # has the project drifted from the harness?
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv lock --check
```

A finding backed by command output beats a finding backed by reading.

## Checklist

### Harness

- [ ] `.django-ai-harness.json` present, and `apply --check` exits 0
- [ ] `AGENTS.md` present and matching the project's actual conventions
- [ ] Files reported as `skipped (local edits)` are intentional divergences, not accidents

### Dependencies and quality

- [ ] `uv.lock` committed and consistent with `pyproject.toml` (`uv lock --check`)
- [ ] Commands run through `uv run`
- [ ] Ruff configured and clean; pre-commit installed
- [ ] CI runs lint, tests, and system checks

### Settings

- [ ] The `config/settings/` split is intact
- [ ] Application code imports `django.conf.settings`, never a settings module directly
- [ ] No runtime settings mutation in business code
- [ ] Secrets come from the environment, and `.envs/` is not committed
- [ ] System checks are registered in **base**, so they run under `config.settings.test`

### Migrations and data

- [ ] `makemigrations --check` is clean, and enforced in CI
- [ ] `max_migration.txt` files are present and current
- [ ] Factories exist for tests; `seed_database` covers local demo data
- [ ] Data migrations are separate from schema migrations

### Architecture (HackSoft)

- [ ] Writes and workflows in services; keyword-only arguments, `full_clean()`,
      `transaction.atomic`
- [ ] Reads in selectors; no state mutation
- [ ] APIs thin: validate, call, serialize — one operation per class
- [ ] No business logic in serializers, forms, signals, `Model.save`, managers or
      querysets
- [ ] Side effects depending on committed rows use `transaction.on_commit`
- [ ] Tests mirror the layers and name the thing under test
- [ ] Database constraints used where the database can enforce the invariant

## Reporting

Group findings by severity and make each one actionable — file, line, and the concrete
change:

1. **Critical** — will break in production, loses data, or leaks secrets
2. **Important** — should be fixed before merge
3. **Minor** — worth doing, not worth blocking

Then a one-line verdict: **Ready** or **Not ready**.

Distinguish what you verified by running something from what you inferred by reading. If
you could not run the checks, say so rather than implying you did.

If the project deliberately diverges from the styleguide, note it once and move on. Do
not re-litigate a decision the team already made.
