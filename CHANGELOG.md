# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version applies to both the distribution and the **overlay contract** written into
`.django-ai-harness.json` of generated projects.

## [Unreleased]

## [2.0.0] - 2026-08-17

A correctness, packaging and maintainability release. Everything the harness promised in
1.x is now enforced by tests and CI.

### Added

- **Installable package.** `uvx django-ai-harness new ~/Projects/app "App"` works with no
  clone. Subcommands: `new`, `wizard`, `apply`, `info`.
- **`apply --check`**, which reports overlay drift and exits non-zero without writing.
  It fails when the overlay would write files, or when a 1.x upgrade is still pending.
  Locally edited managed files are listed and do not fail the check.
- **Upgrade-aware overlay.** Files the overlay owns are tracked in
  `.django-ai-harness.json` with a content hash, so a harness upgrade propagates to files
  you never touched while locally edited files are reported and preserved. `--force`
  overrides.
- **Test suite** for the overlay, the scaffold and the repository invariants; previously
  there was none.
- **Ruff, pre-commit and shellcheck** applied to the harness itself.
- **Biweekly dependency review** (`dx-dependencies.yml`) that checks PyPI, regenerates the
  golden example, runs the tests and opens a pull request.
- **Upstream drift review** now opens or updates a tracking issue instead of writing a
  diff into a log.
- **Release workflow** publishing to PyPI through Trusted Publishing on a `v*` tag.
  `workflow_dispatch` was removed: a manual run would otherwise skip the tag/version
  check and publish whatever was checked out.
- **Bilingual wizard** (English and Spanish) selected with `--lang` or the environment.
- **Agent Skills in generated projects.** `django-hacksoft` and `django-dx-review` are
  written into `skills/` by the overlay, so agents working in the project do not depend
  on a clone of this repository. `django-dx-scaffold` stays in the harness repo.
- **`DATABASES["direct"]`** when PgBouncer is enabled, making `POSTGRES_HOST_DIRECT` a
  live setting: `python manage.py migrate --database=direct`. It carries
  `TEST = {"MIRROR": "default"}` so the test runner does not create a second database.
- Issue templates, pull request template, `CODEOWNERS` and Dependabot configuration.

### Fixed

- **Regeneration is deterministic again.** The overlay no longer shells out to
  `uv add --group dev`, which resolved against PyPI at apply time and wrote `>=` pins.
  Any new release of a DX dependency would have made the golden-example check fail on
  every open pull request. Dependencies now come from a pinned `dev-requirements.txt` and
  are merged into `[dependency-groups].dev` directly. The overlay no longer needs network
  access at all.
- **Marker blocks can no longer corrupt a settings file.** `# >>> django-ai-harness` was a
  prefix of `# >>> django-ai-harness:pgbouncer`, so an unanchored regex could match the
  start of one block and the end of another. Markers are now namespaced and matched with
  line anchors; blocks written by 1.x are migrated automatically.
- **System checks now run in CI.** `django-linear-migrations` and `django-version-checks`
  moved to base settings; in 1.x they were local-only, and `config.settings.test` imports
  base, so their checks never ran during tests. They stay in the *dev* extra and are
  registered behind an `ImportError` guard, so production images that run
  `uv sync --no-dev` still boot.
- **Rich logging extends the upstream configuration** instead of replacing `LOGGING`
  wholesale and silently discarding cookiecutter-django's loggers and formatters.
- **PgBouncer entrypoint reports missing credentials.** Under `set -u`, an unset
  `POSTGRES_USER` aborted the script before the check that was meant to explain it.
- **PgBouncer settings override `HOST`/`PORT`** when `USE_PGBOUNCER` is true, so a
  `DATABASE_URL` that pointed at Postgres does not bypass the pooler.
- **PgBouncer healthcheck** uses `nc -z` instead of `pg_isready`, which is not on PATH
  in the `edoburu/pgbouncer` image. Production `env_file` is a separate Compose fragment
  (`docker-compose.pgbouncer.production.yml`) rather than a comment to edit by hand.
- **`config/urls.py` catches `ImportError`** rather than swallowing every exception.
- **`SECURITY.md` no longer claims `example/.envs/` is committed.** It is not:
  the example is generated with `keep_local_envs_in_vcs=n`.
- Project names and descriptions containing `=` are accepted: cookiecutter is driven
  through its Python API with a context dictionary rather than `key=value` CLI arguments.

### Changed

- Code moved to `src/django_ai_harness/`. `python overlay/apply.py <project>` still works
  from a source checkout; `--harness-root` is accepted and ignored.
- The cookiecutter pin moved from `COOKIECUTTER_PIN` to
  `src/django_ai_harness/data/cookiecutter-django.pin` so it ships in the wheel.
- Library errors are English-only. Only wizard and CLI presentation text is translated.
- Scheduled reviews run on the 1st and the 15th; previously the only scheduled job ran
  weekly and reported nothing.
- `example/uv.lock` is excluded from the byte-for-byte golden diff and verified with
  `uv lock --check` instead, since transitive dependencies resolve freshly.

### Removed

- `pgbouncer.ini` and `userlist.txt.example`. The Compose fragment never mounted them —
  the `edoburu/pgbouncer` image renders its configuration from environment variables — so
  editing them had no effect. Custom-configuration instructions are in the PgBouncer
  README.
- Empty `overlay/files/` and `overlay/patches/` placeholder directories.
- `knowledge/CHANGELOG-practices.md`, consolidated into this file.

### Migration from 1.x

```bash
uvx django-ai-harness apply /path/to/project
# Commit. Then adopt the files 1.x wrote without recording ownership:
uvx django-ai-harness apply /path/to/project --force
cd /path/to/project && uv sync
```

The first run migrates 1.x marker blocks and moves the DX dependencies from `>=` to
`==`. Files 1.x wrote (`AGENTS.md`, templates) are reported as
`skipped (untracked, pre-2.0)` and `--check` stays red until `--force` adopts them.
Review the diff before committing the second run.

### Deferred

- Architecture linter for services / selectors:
  [#1](https://github.com/leohakim/django-ai-harness/issues/1)
- Overlay a professional SaaS `users/` surface:
  [#2](https://github.com/leohakim/django-ai-harness/issues/2)

## [1.2.0] - 2026-08-10

- Guided Textual wizard with per-decision trade-off explanations.
- Single pin source of truth; `keep_local_envs_in_vcs=n` for the golden example.
- CI fails when `example/` drifts.
- PgBouncer Compose binds to `127.0.0.1:6432`; templates are write-if-missing on re-apply.

## [1.1.0] - 2026-08-10

- Opt-in PgBouncer templates and env-gated settings.
- `seed_database` moved under the installed `users` app so the command is discoverable.
- Scaffold files created only when missing.

## [1.0.0] - 2026-08-10

- Initial public release: pinned cookiecutter-django plus an idempotent overlay,
  distilled DX practices, HackSoft architecture skills, and a golden example.

[Unreleased]: https://github.com/leohakim/django-ai-harness/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/leohakim/django-ai-harness/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/leohakim/django-ai-harness/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/leohakim/django-ai-harness/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/leohakim/django-ai-harness/releases/tag/v1.0.0
