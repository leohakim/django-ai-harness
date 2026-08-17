# Book map — *Boost Your Django DX* themes → harness

This is a **mapping of themes**, not a reproduction of the book. Prefer public package docs for how-to details.

| Book theme (edition topics) | Modern harness approach | Where encoded |
|---|---|---|
| Virtualenv + pip-compile / lock | `uv` + `uv.lock` (cookiecutter-django) | upstream |
| Single dependency set; careful upgrades | One project lockfile; `django-version-checks` | overlay deps + settings |
| Python development mode | Document `PYTHONDEVMODE=1` for local; optional system check | `knowledge/dx-practices/devmode.md`, overlay |
| IPython shell | `ipython` (+ existing `ipdb`) | overlay deps |
| django-read-only | Add package + local settings note | overlay |
| Debug toolbar | Already in cookiecutter-django local | upstream |
| Watchman / autoreload | Werkzeug watchdog already; add browser-reload | overlay |
| django-browser-reload | Add + wire middleware/urls in local | overlay |
| Rich terminal output | `django-rich` + RichHandler logging in local settings | overlay |
| EditorConfig + pre-commit | Already present; keep | upstream |
| Black / isort / Flake8 | **Ruff** format+lint (upstream) | upstream |
| pyupgrade / django-upgrade | Ruff UP + django-upgrade hook | upstream |
| DjHTML / curlylint / ESLint / Prettier | djLint upstream; Biome optional if JS appears | knowledge note |
| Settings structure + anti-patterns | Keep cookiecutter split; apply anti-patterns inside | `dx-practices/settings.md` |
| Seed command + Factory Boy | Factory Boy upstream; add `seed_database` | overlay |
| Migration safeguards / linear migrations | pending-migrations test + `django-linear-migrations` in **base** | overlay |
| System checks / version checks | `django-version-checks`, registered in **base** so checks run in CI | overlay |
| Nested project package layout | cookiecutter-django two-tier layout | upstream |
| Build your own tools | document custom pre-commit / checks pattern | `dx-practices/custom-tools.md` |
| Low-RAM Postgres (pooling) | Opt-in PgBouncer + tuning presets; keep the PostgreSQL engine | `dx-practices/postgres-pooling.md`, `--with-pgbouncer` |

Themes from the updated edition (debuggers, Biome, Djade) are tracked as optional upgrades in
[`CHANGELOG.md`](../CHANGELOG.md) when they land in the overlay.
