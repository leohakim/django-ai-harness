# Contributing

Thanks for helping improve Django developer experience for humans and agents alike.

## Setup

```bash
git clone https://github.com/leohakim/django-ai-harness.git
cd django-ai-harness
uv sync --extra wizard
uv run pre-commit install
uv run pytest
```

## What belongs here

- Distilled practices: checklists, configuration, overlay behaviour
- Agent Skills
- Documentation improvements
- Fixes for cookiecutter-django upstream drift

## What does not

- Copyrighted book text or PDFs, including from *Boost Your Django DX*
- Real secrets or production credentials
- Application features unrelated to the harness

## Proposing a practice

Practices in this repository are expected to be **justified, not asserted**. A good
proposal names the problem, the source, and the cost.

1. Open a [practice proposal](https://github.com/leohakim/django-ai-harness/issues/new?template=practice_proposal.yml)
   describing the problem it solves, the source (blog post, package documentation,
   styleguide), and the trade-offs.
2. Once there is agreement, implement it across the layers it touches:
   - `knowledge/` — why it exists and when it applies
   - `src/django_ai_harness/overlay.py` — if every new project should get it
   - `src/django_ai_harness/data/dev-requirements.txt` — if it needs a dependency,
     pinned with `==`
   - `skills/` — if agents should enforce it
   - `docs/` — if humans or agents need new instructions
3. Run `./scripts/refresh-example.sh` and commit the regenerated `example/`.
4. Add a `CHANGELOG.md` entry under `## [Unreleased]`.

## The three invariants

The overlay's tests exist to protect three properties. A change that breaks one of them
will not be merged, even if it is otherwise an improvement.

**Idempotent.** Applying twice produces the same tree.

**Hermetic.** No network access, no dependency resolver, no subprocess at apply time.
This is why DX dependencies are pinned with `==` in a data file rather than resolved.
Version 1.x called `uv add`, and that made regeneration of the golden example depend on
what PyPI happened to hold that day, which would have turned every contributor's pull
request red for reasons unrelated to their change.

**Upgrade-aware.** A file the user edited is reported, never silently overwritten.

## Working on the overlay

```bash
uv run pytest tests/test_overlay.py -v
./scripts/refresh-example.sh
git diff --stat example
```

If `example/` shows a diff you did not intend, the change is not deterministic. Find out
why before continuing.

To try the overlay against a real project without regenerating anything:

```bash
uv run django-ai-harness apply /path/to/some/project --check
```

## Dependency pins

Two sets of pins, updated differently:

| File | Contains | Updated by |
|---|---|---|
| `src/django_ai_harness/data/cookiecutter-django.pin` | The upstream template commit | A human, after reviewing the drift issue |
| `src/django_ai_harness/data/dev-requirements.txt` | DX dependencies installed into projects | The biweekly workflow, reviewed by a human |

Never replace `==` with `>=` in `dev-requirements.txt`.

## Commits and pull requests

Conventional Commits are appreciated (`fix(overlay): …`, `docs: …`, `feat(cli): …`) but
not enforced. Prefer small pull requests that update knowledge, overlay and docs
together, and explain *why* in the description.

CI runs lint, the test suite on Python 3.11–3.13, a full regeneration of `example/`, the
generated project's own test suite against PostgreSQL, and a wheel-contents check.

## Releasing

Maintainers only:

1. Update `version` in `pyproject.toml` and `__version__` in
   `src/django_ai_harness/__init__.py` (a test enforces that they match).
2. Move the `## [Unreleased]` entries into a new version section in `CHANGELOG.md`.
3. Tag and push: `git tag v2.0.1 && git push --tags`.

`release.yml` verifies the tag matches the package version, runs the tests, and publishes
to PyPI via Trusted Publishing.

## Licence

By contributing you agree that your contributions are licensed under the MIT License.
