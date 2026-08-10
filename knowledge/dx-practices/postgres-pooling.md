# PostgreSQL pooling (PgBouncer) — opt-in

Stay on **PostgreSQL** (cookiecutter-django default). Use PgBouncer when RAM pressure from process-per-connection backends matters (small/medium VPS, many gunicorn/Celery workers).

## Why

Each Postgres connection is an OS process (~5–10+ MB). Many app workers × persistent `CONN_MAX_AGE` connections inflate RAM. PgBouncer multiplexes many client connections onto a small pool of real backends.

## Overlay contract

| Piece | Behavior |
|---|---|
| Templates | Always installed under `compose/pgbouncer/` + `docker-compose.pgbouncer.yml` |
| Settings hooks | Always patched into `local.py` / `production.py` (no-op unless `USE_PGBOUNCER=True`) |
| Env activation | Only with `overlay/apply.py --with-pgbouncer` or `WITH_PGBOUNCER=1 ./scripts/new-project.sh …` |

Engine stays `django.db.backends.postgresql`. No MariaDB/Firebird switch.

## Django settings (transaction pooling)

When `USE_PGBOUNCER=True`:

- `CONN_MAX_AGE=0` (do not pin Django connections across requests)
- `DISABLE_SERVER_SIDE_CURSORS=True` (required for transaction pooling)
- Prefer request-scoped transactions (`ATOMIC_REQUESTS` is already on in cookiecutter base)

## Topology

```text
django / celery  →  pgbouncer:6432  →  postgres:5432
migrate / DDL    →  postgres:5432   (bypass pooler)
```

```bash
docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d

# migrate bypass
POSTGRES_HOST=postgres POSTGRES_PORT=5432 USE_PGBOUNCER=False \
  uv run python manage.py migrate
```

## Tuning presets

| File | Target |
|---|---|
| `compose/pgbouncer/postgres/tuning-small.conf` | ~2 GB shared box |
| `compose/pgbouncer/postgres/tuning-medium.conf` | ~4 GB shared box |

Keep Postgres `max_connections` low; raise PgBouncer `max_client_conn` / `default_pool_size` instead.

## Activation checklist

1. Project has cookiecutter Docker compose (`use_docker=y`) or equivalent `postgres` service.
2. Overlay applied (templates present).
3. `--with-pgbouncer` **or** manual env: `USE_PGBOUNCER=True`, `POSTGRES_HOST=pgbouncer`, `POSTGRES_PORT=6432`, `CONN_MAX_AGE=0`.
4. Merge `docker-compose.pgbouncer.yml`.
5. For production compose, point pgbouncer `env_file` at `./.envs/.production/.postgres`.
6. Run migrations against direct Postgres.

## Non-goals

- Not a default for every project (dev without Docker stays simple).
- Not a database engine change.
- Not a substitute for query optimization or missing indexes.
