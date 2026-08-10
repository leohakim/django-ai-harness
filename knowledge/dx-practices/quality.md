# Code quality

- **Ruff** replaces the classic Black + isort + Flake8 trio for speed and one config surface.
- Keep **pre-commit** installed in every clone (`pre-commit install`).
- Keep **django-upgrade** targeting your Django major.
- Template linting: djLint (upstream). If you add a modern JS frontend, prefer **Biome** over legacy ESLint/Prettier pairs.
- Format/lint in CI the same way as pre-commit to avoid “works on my machine”.
