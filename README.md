# django-ai-harness

**Open-source harness** to start Django projects with strong developer experience (DX), HackSoft-style architecture, and instructions that **AI agents** can follow consistently.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/leohakim/django-ai-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/leohakim/django-ai-harness/actions/workflows/ci.yml)

- **Bootstrap:** [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django) at a **pinned commit** (override with `COOKIECUTTER_DJANGO_REF`) + **overlay** idempotente

Practices are inspired by Adam Johnson’s *Boost Your Django DX* (kaizen / tooling / settings / migrations / checks), modernized for 2026 (`uv`, Ruff, etc.), plus [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide) for services/selectors.

> We **do not** redistribute the book. See [docs/book-attribution.md](docs/book-attribution.md).

---

## Why this exists

Starting a Django project “cleanly” usually means remembering dozens of decisions: dependency locking, pre-commit, debug tooling, migration safeguards, where business logic lives, and how agents should behave.

**django-ai-harness** turns that into:

1. A **repeatable bootstrap** (`cookiecutter-django` → overlay).
2. A **knowledge base** agents and humans can read.
3. **Cursor skills** for scaffold / architecture / review.
4. A **golden `example/`** project that CI keeps honest when upstream changes.

### Benefits

| Benefit | What you get |
|---|---|
| Faster greenfield | One script/skill creates a production-oriented Django base + DX extras |
| Consistent AI behavior | `AGENTS.md` + skills reduce “invented” layouts and bad patterns |
| Clean architecture | Services write, selectors read, thin APIs — HackSoft contract |
| Modern DX tooling | Builds on cookiecutter-django’s `uv` + Ruff; adds browser-reload, Rich, read-only shell, linear migrations, version checks, seed command |
| Safer evolution | Overlay is idempotent; `example/` + CI detect cookiecutter-django drift |
| Open source kaizen | Add practices via PRs without rewriting every app from scratch |

More detail: [docs/benefits.md](docs/benefits.md).

---

## Repository layout

```text
django-ai-harness/
├── README.md                 ← you are here
├── docs/                     ← human + agent guides
├── knowledge/                ← distilled practices (no book text)
├── overlay/                  ← applied on top of cookiecutter-django
├── skills/                   ← Cursor Agent Skills
├── scripts/                  ← new-project & refresh-example
├── example/                  ← golden project (generated)
└── .github/workflows/        ← CI + upstream drift checks
```

---

## Requirements

- Python 3.12+ (cookiecutter-django may request a specific minor; follow its `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- [cookiecutter](https://cookiecutter.readthedocs.io/) (`brew install cookiecutter` or `uv tool install cookiecutter`)
- Git
- Optional: [Cursor](https://cursor.com/) to use the bundled skills
- Optional: Docker if you enable Docker in cookiecutter prompts

---

## Quick start — new project from zero

```bash
# 1) Get the harness
git clone https://github.com/leohakim/django-ai-harness.git
cd django-ai-harness

# 2) Create a project (cookiecutter-django latest + overlay)
./scripts/new-project.sh ~/Projects/my_app

# 3) Enter the project and sync
cd ~/Projects/my_app
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Full walkthrough (prompts, first HackSoft app, checklist): **[docs/getting-started.md](docs/getting-started.md)**.

Human-oriented notes: [docs/for-humans.md](docs/for-humans.md).  
Agent-oriented contract: [docs/for-agents.md](docs/for-agents.md).

---

## What the overlay adds

cookiecutter-django already ships strong defaults (`uv`, Ruff, pre-commit, debug toolbar, Factory Boy, DRF option, etc.).

The harness overlay then adds / standardizes:

- `AGENTS.md` + pointers to HackSoft + DX rules for AI agents
- `django-browser-reload`, `django-rich`, `django-read-only`, `ipython`
- `django-linear-migrations`, `django-version-checks`
- `seed_database` management command pattern + pending-migrations test
- HackSoft app skeleton (`services.py`, `selectors.py`, thin API stubs)
- Documentation of settings anti-patterns **inside** `config/settings/*` (we keep the split)

Details: [docs/overlay.md](docs/overlay.md).

---

## Using with AI agents (Cursor)

1. Clone this repo (or add it as a reference checkout).
2. Install / copy skills from `skills/` into your Cursor skills path, **or** open this repo and `@`-mention the skill folders.
3. Ask the agent to run **`django-dx-scaffold`** for a new app.
4. For feature work, enforce **`django-hacksoft`**.
5. Before PRs, run **`django-dx-review`**.

See [docs/for-agents.md](docs/for-agents.md).

---

## Golden example

`example/` is a non-interactive regeneration of cookiecutter-django + overlay. Refresh with:

```bash
./scripts/refresh-example.sh
```

CI runs checks against this tree so upstream template changes surface early.

---

## Updating practices

See [docs/updating.md](docs/updating.md) for:

- Adding a new practice to `knowledge/` + overlay
- Re-applying the overlay to an existing project
- Tracking cookiecutter-django upgrades

---

## Open source

- License: [MIT](LICENSE)
- Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Contribute: [CONTRIBUTING.md](CONTRIBUTING.md)

Third-party projects keep their own licenses (cookiecutter-django, HackSoft styleguide, packages). Attribution: [docs/book-attribution.md](docs/book-attribution.md).

---

## Status

v1 focuses on **bootstrap + knowledge + agent skills + golden example**. Production deployment still follows cookiecutter-django’s docs for your chosen stack (Docker, cloud provider, etc.).
