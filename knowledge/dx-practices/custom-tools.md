# Custom tools

When a repeated mistake appears:

1. Prefer an existing Ruff/django-upgrade/pre-commit hook.
2. Else add a small pre-commit `local` hook or Django system check.
3. Document the *why* in `knowledge/` and encode it in `overlay/` if every project should inherit it.

This is the kaizen loop the harness exists to support.
