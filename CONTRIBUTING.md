# Contributing to django-ai-harness

Thanks for helping improve Django DX for humans and AI agents.

## What belongs here

- Distilled practices (checklists, configs, overlay patches)
- Skills for Cursor agents
- Documentation improvements
- Fixes when cookiecutter-django upstream drifts

## What does **not** belong here

- Copyrighted book text or PDFs (including *Boost Your Django DX*)
- Real secrets or private production credentials
- Unrelated application features

Note: the golden `example/` is generated with `keep_local_envs_in_vcs=n`, so `.envs/`
is not committed. Never commit real secrets.

## How to propose a new practice

1. Open an issue describing the practice, the problem it solves, and the source (blog, package docs, styleguide).
2. Add or update:
   - `knowledge/` (why + when)
   - `knowledge/book-map.md` if it maps from the book
   - `overlay/` if projects should get it automatically
   - `docs/` if humans/agents need new instructions
3. Run `scripts/refresh-example.sh` and ensure CI-oriented checks still pass.
4. Open a PR with a short rationale (prefer *why* over *what*).

## Local setup

```bash
git clone https://github.com/leohakim/django-ai-harness.git
cd django-ai-harness
# Optional: regenerate the golden example
./scripts/refresh-example.sh
```

## License

By contributing, you agree your contributions are licensed under the MIT License.
