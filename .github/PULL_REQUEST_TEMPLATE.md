## What changes

<!-- One or two sentences. Prefer *why* over *what*: the diff already says what. -->

## Why

<!-- The problem this solves, and the source if it comes from one (blog post, package
     documentation, styleguide). Practices in this repository are expected to be
     justified, not just asserted. -->

## Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check . && uv run ruff format --check .` passes
- [ ] If the overlay changed: `./scripts/refresh-example.sh` was run and `example/` is committed
- [ ] If a practice changed: `knowledge/` explains the reasoning
- [ ] If behaviour changed: `CHANGELOG.md` has an entry
- [ ] No copyrighted book text, and no real secrets
