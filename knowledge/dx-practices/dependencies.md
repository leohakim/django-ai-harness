# Dependencies and environments

## In a generated project

- Use **`uv`** for install, sync and lock. Commit `uv.lock`.
- Keep a **single lockfile** for the application; use the `dev` dependency group for
  tooling that never ships.
- Add packages with `uv add` / `uv add --group dev`. Never hand-edit `uv.lock`.
- Use `uv run` rather than activating a virtual environment, so every command runs against
  the locked set.
- Assert the lockfile is current in CI with `uv lock --check`.
- Schedule upgrades deliberately. `django-version-checks` makes the expected Python
  version explicit and fails a system check when the environment disagrees, which is
  cheaper than debugging a subtle difference later.
- Enable Python development mode when chasing something odd: `export PYTHONDEVMODE=1`.

## In the harness

The overlay does **not** run a resolver. The DX dependencies it installs are pinned with
`==` in `src/django_ai_harness/data/dev-requirements.txt` and written straight into
`[dependency-groups].dev`.

This looks stricter than necessary until you consider what the alternative does. Version
1.x called `uv add --group dev`, which resolved against PyPI at apply time and wrote
`>=` pins. Regenerating the golden example on two different days then produced two
different trees — so the CI check that compares the committed example against a fresh
regeneration would start failing the moment any of those six packages published a
release, on every open pull request, for reasons unrelated to the change under review.

Pinning moves that from an ambient failure to a scheduled decision: the biweekly
`dx-dependencies` workflow checks PyPI, regenerates, runs the tests, and opens a pull
request a human reviews.

The general principle applies well beyond this repository: **a build step that reaches
the network is a build step whose output you do not control.**
