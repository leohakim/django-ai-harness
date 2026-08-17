# For AI agents

## Goal

Produce and maintain Django projects that:

1. Originate from cookiecutter-django at a pinned commit plus the django-ai-harness
   overlay.
2. Keep business logic in services and selectors (HackSoft Django Styleguide).
3. Preserve the developer-experience gates: Ruff, pre-commit, system checks, migration
   safeguards.

## Required reading order

1. The project's own `AGENTS.md` (generated projects always have one)
2. This file
3. `knowledge/architecture/hacksoft.md`
4. `knowledge/cookiecutter-django.md`
5. `docs/overlay.md`

## Scaffolding a new project

Use the [`django-dx-scaffold`](../skills/django-dx-scaffold/SKILL.md) skill.

```bash
uvx django-ai-harness new <target_directory> "<Project Name>"
```

Add flags rather than post-editing generated files:
`--use-celery y`, `--rest-api "Django Ninja"`, `--with-pgbouncer`, `--use-docker n`.

Verify afterwards:

```bash
test -f <target>/AGENTS.md
test -f <target>/.django-ai-harness.json
uvx django-ai-harness apply <target> --check   # must exit 0
```

Do not invent an alternative project layout. Do not skip the overlay.

## Implementing features

Use the [`django-hacksoft`](../skills/django-hacksoft/SKILL.md) skill.

| Behaviour | Layer |
|---|---|
| Writes, workflows, side effects | `services.py` |
| Reads, filtering, visibility | `selectors.py` |
| HTTP input and output | thin APIs with nested serializers |
| Simple non-relational invariants | `Model.clean` or a database constraint |
| Async entry point | a Celery task that calls a service |

Business rules never live in views, serializers, forms, signals, `Model.save`, or custom
managers and querysets. Tests mirror the layers.

## Reviewing

Use the [`django-dx-review`](../skills/django-dx-review/SKILL.md) skill before claiming a
change is done.

## Upgrading a project

```bash
uvx django-ai-harness apply .
```

Read the output. `skipped (local edits)` means the user edited a file the overlay owns —
surface that to the user and let them decide; never pass `--force` on your own initiative.

## Forbidden

- Copying copyrighted book text into any repository
- Putting domain rules in views, serializers, signals, or `Model.save`
- Replacing the `config/settings/` split with a single settings module
- Skipping the overlay on a project that claims to use this harness
- Loosening the `==` pins in `dev-requirements.txt` to `>=`
- Editing `.django-ai-harness.json` by hand
