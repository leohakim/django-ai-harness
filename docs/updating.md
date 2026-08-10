# Updating

## Update the harness itself

```bash
cd django-ai-harness
git pull
./scripts/refresh-example.sh   # optional, for contributors
```

## Re-apply overlay to an existing project

```bash
python /path/to/django-ai-harness/overlay/apply.py /path/to/project
cd /path/to/project
uv sync
uv run pre-commit install
uv run pytest
```

Review the diff: overlay uses markers like `# >>> django-ai-harness` so you can spot insertions.

## Track cookiecutter-django upgrades

1. Compare against tip: `COOKIECUTTER_DJANGO_REF=master ./scripts/refresh-example.sh`
2. Fix overlay if upstream renamed files/settings.
3. Bump the default pin in `scripts/new-project.sh` / `scripts/refresh-example.sh` when ready.
4. Document breaking changes in `knowledge/CHANGELOG-practices.md`.

CI workflow `upstream-cookiecutter.yml` regenerates against **`master`** on a schedule so tip drift surfaces even while day-to-day scripts stay pinned.

## Add a new practice

1. Write the *why* in `knowledge/dx-practices/` or `knowledge/architecture/`.
2. Map it in `knowledge/book-map.md` if relevant.
3. Encode it in `overlay/` when every new project should get it.
4. Update docs + changelog.
5. Open a PR (see CONTRIBUTING.md).
