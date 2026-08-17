<div align="center">

# django-ai-harness

**Start Django projects with strong developer experience, a real architecture contract, and instructions AI agents actually follow.**

[![CI](https://github.com/leohakim/django-ai-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/leohakim/django-ai-harness/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/django-ai-harness.svg)](https://pypi.org/project/django-ai-harness/)
[![Python](https://img.shields.io/pypi/pyversions/django-ai-harness.svg)](https://pypi.org/project/django-ai-harness/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

```bash
uvx django-ai-harness new ~/Projects/my_shop "My Shop"
```

That is a complete, production-oriented Django project: [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django)
at a pinned commit, plus an idempotent overlay that adds developer-experience tooling,
a [HackSoft](https://github.com/HackSoftware/Django-Styleguide)-style service/selector
architecture, and an `AGENTS.md` contract your AI agents can follow.

---

## Why this exists

Starting a Django project "properly" means re-making the same two dozen decisions:
dependency locking, pre-commit, debug tooling, migration safeguards, where business logic
lives, and — increasingly — how coding agents are supposed to behave in the repository.

Most answers to this are a template you fork and then slowly drift away from.
**django-ai-harness is not a fork.** It pins cookiecutter-django at an exact commit and
applies an overlay on top, so upstream improvements stay reachable and the harness's own
opinions stay reviewable as a diff.

| | |
|---|---|
| **Repeatable bootstrap** | One command produces the same project today and in six months |
| **Consistent agent behaviour** | `AGENTS.md` plus Agent Skills replace "please follow my conventions" in every prompt |
| **Real architecture** | Services write, selectors read, interfaces stay thin |
| **Upgradable** | `django-ai-harness apply .` propagates harness improvements without clobbering your edits |
| **Self-checking** | A golden `example/` is regenerated in CI, so upstream drift surfaces as a failing build, not as a surprise |

---

## Install

Nothing to clone. With [uv](https://docs.astral.sh/uv/):

```bash
uvx django-ai-harness --help
```

Or install it permanently:

```bash
uv tool install 'django-ai-harness[wizard]'
```

The harness itself runs on Python 3.11+. Generated projects target whatever the pinned
cookiecutter-django targets (currently 3.14).

---

## Usage

### Create a project

```bash
uvx django-ai-harness new ~/Projects/my_shop "My Shop"
cd ~/Projects/my_shop
uv sync
docker compose -f docker-compose.local.yml up -d
uv run python manage.py migrate
uv run python manage.py runserver
```

Every cookiecutter choice is available as a flag:

```bash
uvx django-ai-harness new ~/Projects/my_api "My API" \
  --use-celery y --cloud-provider AWS --frontend-pipeline Webpack
```

Without Docker, supply `POSTGRES_*` or `DATABASE_URL` yourself:

```bash
uvx django-ai-harness new ~/Projects/my_api "My API" --use-docker n
```

### Guided wizard

```bash
uvx --from 'django-ai-harness[wizard]' django-ai-harness wizard
```

A [Textual](https://textual.textualize.io/) TUI that walks through each decision and
explains what it **adds**, what it **leaves out**, and the practical implication.
Available in English and Spanish (`--lang en|es`, or follow your `LANG`).

### Upgrade an existing project

```bash
uvx django-ai-harness apply .          # apply or upgrade the overlay
uvx django-ai-harness apply . --check  # exit 1 if the project drifted; writes nothing
```

`--check` is designed for your own CI: it fails the build when a project has fallen
behind the harness version it was generated with.

### Inspect what you would get

```bash
uvx django-ai-harness info
```

---

## What the overlay adds

cookiecutter-django already ships excellent defaults (`uv`, Ruff, pre-commit, debug
toolbar, Factory Boy, an optional DRF setup). The overlay adds the layer above that:

| Area | What you get |
|---|---|
| **Agent contract** | `AGENTS.md` describing the architecture, the DX rules, and where things live |
| **Architecture** | `harness_templates/app_skeleton/` — services, selectors, thin APIs with nested serializers |
| **Local DX** | `django-browser-reload`, `django-rich` console logging, `django-read-only`, IPython `shell_plus` |
| **Migration safety** | `django-linear-migrations` with `max_migration.txt`, plus a pending-migrations test |
| **Environment safety** | `django-version-checks` pinned to the project's own `.python-version` |
| **Seed data** | A `seed_database` management command wired to Factory Boy |
| **Settings hygiene** | Documented anti-patterns *inside* the settings split, which is kept intact |
| **Connection pooling** | Opt-in PgBouncer with a `direct` database alias for migrations (`--with-pgbouncer`) |

System checks (`django-linear-migrations`, `django-version-checks`) are registered in
**base** settings so they also run under `config.settings.test`, and therefore in CI.
Purely local tooling stays in **local** settings.

Details: [docs/overlay.md](docs/overlay.md).

---

## Design guarantees

The overlay makes three promises, each covered by tests:

**Idempotent.** Running it twice produces the same tree. Settings patches live inside
uniquely named marker blocks (`# >>> django-ai-harness:local`) that are replaced in
place.

**Hermetic.** It never touches the network and never invokes a dependency resolver. The
DX dependencies it installs are pinned with `==` in
[`dev-requirements.txt`](src/django_ai_harness/data/dev-requirements.txt). A release on
PyPI cannot silently change what you get.

**Upgrade-aware.** Every file the overlay owns is recorded in `.django-ai-harness.json`
with the hash of the content it last wrote:

| File state | What `apply` does |
|---|---|
| missing | writes it |
| already matches | nothing |
| matches what the overlay last wrote | updates it — harness upgrades propagate |
| you edited it | skips it and tells you (`--force` overrides) |
| existed before the overlay | never touched |

---

## Using it with AI agents

Generated projects carry an `AGENTS.md` read by Claude Code, Cursor, Codex, Copilot and
anything else honouring the convention.

The [`skills/`](skills) directory holds three Agent Skills, in the portable
`SKILL.md` format:

| Skill | Use it for |
|---|---|
| [`django-dx-scaffold`](skills/django-dx-scaffold/SKILL.md) | Creating a new project the harness way |
| [`django-hacksoft`](skills/django-hacksoft/SKILL.md) | Implementing and reviewing feature work |
| [`django-dx-review`](skills/django-dx-review/SKILL.md) | Auditing a project before a pull request |

Copy them into your agent's skills directory, or point the agent at this repository.
See [docs/for-agents.md](docs/for-agents.md).

---

## Repository layout

```text
django-ai-harness/
├── src/django_ai_harness/   the package: CLI, overlay, scaffold, wizard, pinned data
├── knowledge/               why each practice exists (no book text)
├── skills/                  portable Agent Skills
├── docs/                    guides for humans and agents
├── example/                 golden project, regenerated and verified by CI
├── tests/                   the overlay's own test suite
└── scripts/                 maintenance entry points for contributors
```

---

## How this maintains itself

| Schedule | Workflow | What it does |
|---|---|---|
| Every push and PR | [`ci.yml`](.github/workflows/ci.yml) | Lint, tests on 3.11–3.13, regenerates `example/` and fails on any diff, runs the generated project's own test suite against PostgreSQL, verifies the wheel ships its data files |
| 1st and 15th | [`dx-dependencies.yml`](.github/workflows/dx-dependencies.yml) | Reviews the pinned DX dependencies against PyPI, regenerates, tests, and **opens a pull request** |
| 1st and 15th | [`upstream-cookiecutter.yml`](.github/workflows/upstream-cookiecutter.yml) | Regenerates against cookiecutter-django `master` and **opens or updates a tracking issue** when upstream drifts |
| On a `v*` tag | [`release.yml`](.github/workflows/release.yml) | Verifies the tag matches the version, then publishes to PyPI via Trusted Publishing |

Nothing merges itself. The automation prepares reviewable work; a human decides.

---

## Credits and attribution

The practices here are distilled from public sources and original work:

- **[cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django)** generates the project. Its licence covers the generated scaffolding.
- **[HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide)** (MIT, © HackSoft) is the basis of the architecture guidance.
- **[*Boost Your Django DX*](https://adamj.eu/books/) by Adam Johnson** inspired the DX themes. This repository contains **no book text** — only original checklists and configuration. If these topics help you, buy the book.

Full notes: [docs/book-attribution.md](docs/book-attribution.md).

---

## Contributing

Practices should be justified, not asserted. Open an issue describing the problem and
the source before a large pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md).

```bash
git clone https://github.com/leohakim/django-ai-harness.git
cd django-ai-harness
uv sync --extra wizard
uv run pre-commit install
uv run pytest
```

Licensed under the [MIT License](LICENSE).
