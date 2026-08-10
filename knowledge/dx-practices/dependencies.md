# Dependencies & environments

- Use **`uv`** for create/sync/lock (`uv.lock` committed).
- Prefer a **single lockfile** for the app; use dependency groups (`dev`) for DX tools.
- Add packages with `uv add` / `uv add --group dev`, never hand-edit lockfiles.
- Schedule periodic upgrades; use `django-version-checks` to keep Python/Django expectations explicit.
- Enable Python development mode locally when debugging subtle issues: `export PYTHONDEVMODE=1`.
