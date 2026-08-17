# Guided wizard

```bash
uvx --from 'django-ai-harness[wizard]' django-ai-harness wizard
```

From a source checkout: `./scripts/new-project-tui.sh`.

A [Textual](https://textual.textualize.io/) TUI for people who would rather understand a
decision than look up a flag.

## What it covers

- Project identity: name, target directory (which derives the package slug), author,
  domain
- Docker Compose
- API stack: DRF, Django Ninja, or none
- Celery, frontend pipeline, CI, WhiteNoise, Sentry, cloud provider
- PgBouncer — shown only when Docker is enabled, because the pooler lives in the Compose
  topology

## How it explains a choice

Every option states three things, because a scaffolding decision is a trade-off, not a
preference:

- **Adds** — what you gain by choosing it
- **Leaves out** — what you give up
- **Implication** — what it means in day-to-day work

Technical names (Docker, DRF, Celery, WhiteNoise) stay in English in every language,
because that is how the ecosystem refers to them.

## Language

```bash
uvx django-ai-harness --lang es wizard
```

Without `--lang`, the wizard follows `DJANGO_AI_HARNESS_LANG`, then `LC_ALL`/`LANG`, then
falls back to English.

## Non-interactive equivalent

The wizard is a front-end over exactly the same code path as `new`, so anything it can do
is scriptable:

```bash
uvx django-ai-harness new ~/Projects/my_app "My App" --use-celery y --with-pgbouncer
```

Agents should prefer `new`. See [for-agents.md](for-agents.md).
