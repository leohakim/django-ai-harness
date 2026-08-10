---
name: django-dx-review
description: Audit a Django project for django-ai-harness DX and HackSoft architecture compliance. Use before PRs, after scaffolding, or when asked to review Django DX.
---

# django-dx-review

## Goal

Produce a defect-first review of DX + architecture compliance.

## Checklist

### Bootstrap / harness

- [ ] Started from cookiecutter-django or clearly documented equivalent
- [ ] `.django-ai-harness.json` present if overlay applied
- [ ] `AGENTS.md` present and accurate

### Dependencies & quality

- [ ] `uv.lock` present and used via `uv sync` / `uv run`
- [ ] Ruff configured; pre-commit present
- [ ] CI runs lint/tests/checks

### DX packages (local)

- [ ] Debug toolbar available locally (cookiecutter default)
- [ ] browser-reload / read-only / linear-migrations / version-checks considered

### Settings

- [ ] No app code imports project settings module directly
- [ ] No runtime settings mutation in business code
- [ ] Secrets via env

### Migrations & data

- [ ] Pending migrations test or `makemigrations --check` in CI
- [ ] Factories for tests; seed command for local demos when needed

### HackSoft architecture

- [ ] Writes in services
- [ ] Reads in selectors
- [ ] Thin APIs
- [ ] Tests mirror layers
- [ ] No domain logic in serializers/signals/`save`

## Output format

1. **Critical** issues (must fix)
2. **Important** issues (should fix before merge)
3. **Minor** / suggestions
4. Short verdict: Ready / Not ready
