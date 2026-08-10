# Models, migrations, seeds

- Generate test/dev data with **Factory Boy**.
- Provide a **`seed_database`** management command for local demos.
- Fail CI when migrations are missing (`makemigrations --check`).
- Use **django-linear-migrations** to avoid merge migration chaos on mainline branches.
- Never commit auto-named nonsense migrations without review.
