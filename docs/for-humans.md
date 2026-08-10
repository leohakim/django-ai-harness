# For humans

## Day-to-day

Treat **django-ai-harness** as your Django “standard library of process”:

- Clone once, update often (`git pull`).
- Create apps with `./scripts/new-project.sh`.
- Read `knowledge/` when unsure *why* a tool exists.
- Send agents to `docs/for-agents.md` instead of re-explaining preferences.

## Working inside a generated project

The generated project is a normal cookiecutter-django app plus overlay files:

- Follow the project’s own README for Docker/deploy.
- Follow `AGENTS.md` for architecture.
- Re-apply overlay after major harness upgrades:

```bash
python /path/to/django-ai-harness/overlay/apply.py .
uv sync
```

## Cursor skills

Copy or symlink `skills/*` into your personal Cursor skills directory, or keep the harness repo open and reference skills explicitly.

## Contributing improvements

See [../CONTRIBUTING.md](../CONTRIBUTING.md). Prefer small PRs that update knowledge + overlay + docs together.
