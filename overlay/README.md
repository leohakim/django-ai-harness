# Overlay

Run:

```bash
python overlay/apply.py /path/to/project --harness-root /path/to/django-ai-harness
# Optional: activate PgBouncer envs (still PostgreSQL)
python overlay/apply.py /path/to/project --harness-root /path/to/django-ai-harness --with-pgbouncer
```

See [../docs/overlay.md](../docs/overlay.md) and [../knowledge/dx-practices/postgres-pooling.md](../knowledge/dx-practices/postgres-pooling.md).
