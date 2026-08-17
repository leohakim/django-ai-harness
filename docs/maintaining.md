# Maintaining

Notes for whoever holds the keys. Day-to-day contribution lives in
[CONTRIBUTING.md](../CONTRIBUTING.md).

## Pending setup

Two one-time configuration steps are not done yet. Neither blocks development, and both
block something specific when the time comes.

- [ ] **PyPI Trusted Publishing.** `release.yml` publishes through OIDC and stores no API
      token, which means the publisher has to be registered on PyPI first. Until it is,
      pushing a `v*` tag runs the build and then fails at the publish step.

      Configure it at
      <https://pypi.org/manage/project/django-ai-harness/settings/publishing/> with:

      | Field | Value |
      |---|---|
      | Owner | `leohakim` |
      | Repository | `django-ai-harness` |
      | Workflow | `release.yml` |
      | Environment | `pypi` |

      For the very first release the project does not exist on PyPI yet, so use the
      [pending publisher](https://pypi.org/manage/account/publishing/) form instead —
      it reserves the name and the publisher together.

      Do this **before** tagging `v2.0.0`.

- [ ] **Enable GitHub Discussions.** `.github/ISSUE_TEMPLATE/config.yml` sends "question
      or idea" traffic to Discussions, and blank issues are disabled. If Discussions is
      off, that contact link 404s and people have nowhere to ask.

      Either enable it in *Settings → General → Features → Discussions*, or delete the
      Discussions entry from `config.yml`. Enabling it is the better answer: it keeps
      the issue tracker for defects and proposals.

## Known upstream constraint: Docker during generation

`cookiecutter-django`'s post-generation hook populates `pyproject.toml` by running `uv`.
When `use_docker=y` — the default, and what `refresh-example.sh` uses — it does that
**inside a container** it builds from `compose/local/uv/Dockerfile`:

```python
# hooks/post_gen_project.py, cookiecutter-django @ 2026.8.9
if "{{ cookiecutter.use_docker }}".lower() == "y":
    ...
    uv_cmd = ["docker", "run", "--rm", "-v", f"{current_path}:/app", uv_image_tag, "uv"]
else:
    uv_cmd = ["uv"]
```

So Docker is required at **generation** time, not only to run the Compose stack. With
`--use-docker n` the hook runs `uv` on the host and Docker is not involved at all.

This is upstream behaviour; the harness does not control it. Two consequences worth
knowing before someone opens an issue:

- **Exit status 137.** The container gets OOM-killed and generation aborts with
  `Error installing local dependencies: ... returned non-zero exit status 137`. It is
  transient — retrying usually works. If it recurs, raise Docker's memory limit. This
  happened once while preparing 2.0.
- **CI is unaffected.** GitHub-hosted runners ship Docker, so `refresh-example.sh` works
  in `ci.yml`, `dx-dependencies.yml` and `upstream-cookiecutter.yml` without extra setup.

If upstream ever drops the container step, the `--use-docker n` caveat above and the
requirements notes in [getting-started.md](getting-started.md) can be simplified.

## Scheduled work

| When | Workflow | Produces | Your job |
|---|---|---|---|
| Push / PR | `ci.yml` | Pass or fail | Keep it green |
| 1st & 15th | `dx-dependencies.yml` | A pull request bumping the pinned DX dependencies | Review the diff, check CI, merge |
| 1st & 15th | `upstream-cookiecutter.yml` | An issue labelled `upstream-drift` | Decide whether to bump the cookiecutter pin |
| `v*` tag | `release.yml` | A PyPI release and a GitHub release | Tag deliberately |

Nothing merges itself. If a scheduled pull request sits unreviewed the next run updates
the same branch rather than opening a second one.

## Bumping the cookiecutter pin

The drift issue tells you upstream moved. It does not tell you to follow.

```bash
COOKIECUTTER_DJANGO_REF=master ./scripts/refresh-example.sh
git diff --stat example
```

1. Read the diff. Look for renamed files or settings the overlay patches — that is what
   breaks first.
2. Fix the overlay, and add a test for whatever broke.
3. Update `src/django_ai_harness/data/cookiecutter-django.pin` to an exact SHA. Never a
   branch name: the pin is the reason generation is reproducible.
4. Regenerate, run the full suite, and record the change in `CHANGELOG.md`.

## Releasing

1. Update `version` in `pyproject.toml` and `__version__` in
   `src/django_ai_harness/__init__.py`. A test fails if they disagree, and another fails
   if `CHANGELOG.md` has no section for the new version.
2. Move the `## [Unreleased]` entries into a dated version section.
3. Tag and push:

   ```bash
   git tag v2.0.1
   git push origin v2.0.1
   ```

`release.yml` verifies that the tag matches the package version before it builds, so a
mismatched tag fails fast instead of publishing the wrong thing.

## Labels

Created automatically on first use by the workflows, but worth defining with colours and
descriptions up front:

| Label | Used by |
|---|---|
| `dependencies` | `dx-dependencies.yml`, Dependabot |
| `upstream-drift` | `upstream-cookiecutter.yml` |
| `bug`, `practice` | Issue templates |
