# For AI agents

## Goal

Produce and maintain Django projects that:

1. Originate from **cookiecutter-django (pinned ref)** + **django-ai-harness overlay**.
2. Keep business logic in **services/selectors** (HackSoft).
3. Preserve DX gates (Ruff, pre-commit, checks, migration safeguards).

## Required reading order

1. Repo root `AGENTS.md`
2. This file
3. `knowledge/cookiecutter-django.md`
4. `knowledge/architecture/hacksoft.md`
5. `knowledge/book-map.md`
6. `overlay/README.md`

## Scaffolding a new project

Use skill `skills/django-dx-scaffold/SKILL.md`:

1. Ensure `uv` and `cookiecutter` exist.
2. Run `scripts/new-project.sh <target_dir>` from the harness root (preferred), or cookiecutter + `overlay/apply.py`.
3. Do **not** invent a custom project layout when the template already provides one.
4. After generation: `uv sync`, migrate, run `manage.py check`, summarize next steps for the user.

## Implementing features

Use skill `skills/django-hacksoft/SKILL.md`:

- Writes → services
- Reads → selectors
- HTTP → thin APIs + nested serializers
- Celery → thin tasks calling services
- Tests mirror layers

## Reviewing

Use skill `skills/django-dx-review/SKILL.md` before claiming “done”.

## Forbidden

- Copying copyrighted book text into the repo or generated projects
- Putting domain rules in views/serializers/signals/`Model.save`
- Replacing cookiecutter settings split with a single mega-settings file “because the book said so” — instead apply anti-patterns *within* `config/settings/`
- Skipping the overlay on greenfield projects that claim to use this harness
