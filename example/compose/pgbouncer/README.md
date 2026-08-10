# PgBouncer (opt-in)

Keep **PostgreSQL** as the database engine (cookiecutter-django compatible). Add PgBouncer in front to cut RAM from process-per-connection backends.

## Enable

1. Ensure the project was generated with `use_docker=y` (cookiecutter), or adapt the compose fragment to your stack.
2. Apply overlay with `--with-pgbouncer` **or** set env vars manually (below).
3. Merge the compose fragment:

```bash
docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d
# production:
docker compose -f docker-compose.production.yml -f docker-compose.pgbouncer.yml up -d
```

4. Point the app at the pooler:

```bash
USE_PGBOUNCER=True
POSTGRES_HOST=pgbouncer
POSTGRES_PORT=6432
CONN_MAX_AGE=0
```

Keep a direct path for migrations/admin ops:

```bash
# one-off migrate bypassing the pooler
POSTGRES_HOST=postgres POSTGRES_PORT=5432 USE_PGBOUNCER=False \
  uv run python manage.py migrate
```

Or, with Docker:

```bash
docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml \
  run --rm -e POSTGRES_HOST=postgres -e POSTGRES_PORT=5432 -e USE_PGBOUNCER=False \
  django python manage.py migrate
```

## Django requirements (transaction pooling)

- `pool_mode = transaction` (default in this template)
- `CONN_MAX_AGE=0` (enforced by overlay when `USE_PGBOUNCER=True`)
- `DISABLE_SERVER_SIDE_CURSORS=True` (same)
- Prefer `ATOMIC_REQUESTS` (already on in cookiecutter base) or explicit transactions

## Postgres tuning

Mount one of:

- `postgres/tuning-small.conf` — ~2 GB shared VPS
- `postgres/tuning-medium.conf` — ~4 GB shared VPS

Example volume on the `postgres` service:

```yaml
volumes:
  - ./compose/pgbouncer/postgres/tuning-small.conf:/etc/postgresql/conf.d/harness-tuning.conf:ro
```

Lower `max_connections` on Postgres; let PgBouncer absorb client concurrency.

## Files

| Path | Role |
|---|---|
| `docker-compose.pgbouncer.yml` | Compose merge fragment (project root) |
| `compose/pgbouncer/entrypoint.sh` | Maps `POSTGRES_*` → edoburu `DB_*` |
| `compose/pgbouncer/pgbouncer.ini` | Reference config (bare-metal / custom image) |
| `compose/pgbouncer/userlist.txt.example` | Auth file example for ini-based setups |
| `compose/pgbouncer/postgres/*.conf` | Optional Postgres presets |

For production compose, override `pgbouncer.env_file` to `./.envs/.production/.postgres`.
The published port is bound to `127.0.0.1:6432` by default (not all interfaces).
