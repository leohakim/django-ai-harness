# Guided project wizard (TUI)

Launch:

```bash
./scripts/new-project-tui.sh
```

Requires `uv`, `cookiecutter`, and a terminal that supports modern TUI apps.

## What it covers

- Project identity (name, path/slug, author, domain)
- Docker Compose
- API stack (DRF / Django Ninja / None)
- Celery, frontend pipeline, CI, WhiteNoise, Sentry, cloud provider
- Optional PgBouncer (only when Docker is enabled)

Each decision shows **+ adds**, **− leaves out**, and practical implications (Spanish copy,
English labels like Docker / DRF / Celery).

## Non-interactive alternative

```bash
./scripts/new-project.sh ~/Projects/my_app "My App"
```

Agents should prefer the non-interactive script or `scripts/lib/cli_scaffold.py`.
