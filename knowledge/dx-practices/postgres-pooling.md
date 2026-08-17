# PostgreSQL connection pooling (PgBouncer) — opt-in

Stay on **PostgreSQL**. Add PgBouncer when memory pressure from process-per-connection
backends is what hurts: a small or medium VPS, many Gunicorn or Celery workers, or a
managed PostgreSQL with a low connection cap.

## Why

Every PostgreSQL connection is an operating-system process costing roughly 5–10 MB. Many
application workers, each holding a persistent connection through `CONN_MAX_AGE`,
multiply that. PgBouncer multiplexes many client connections onto a small pool of real
backends.

It is not a substitute for indexes or query optimisation. If your problem is slow
queries, pooling will not help.

## Overlay contract

| Piece | Behaviour |
|---|---|
| Templates | Always installed under `compose/pgbouncer/` and `docker-compose.pgbouncer.yml` |
| Settings | Always patched into `local.py` and `production.py`, inert unless `USE_PGBOUNCER=True` |
| Env activation | Only with `django-ai-harness apply . --with-pgbouncer` or `new --with-pgbouncer` |

The engine stays `django.db.backends.postgresql`.

## Django settings under transaction pooling

When `USE_PGBOUNCER=True` the overlay sets:

- `CONN_MAX_AGE=0` — a persistent Django connection would pin a pooled server connection
  and defeat the purpose.
- `DISABLE_SERVER_SIDE_CURSORS=True` — server-side cursors cannot survive across
  transactions, and in transaction mode each transaction may land on a different backend.
- `DATABASES["direct"]` — an unpooled alias for DDL, carrying
  `TEST = {"MIRROR": "default"}` so the test runner does not try to create a second test
  database.

`ATOMIC_REQUESTS` is already enabled by cookiecutter-django and pairs well with
transaction pooling.

## Topology

```text
django / celery  →  pgbouncer:6432  →  postgres:5432
migrate / DDL    →  postgres:5432      (bypasses the pooler)
```

```bash
docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d
uv run python manage.py migrate --database=direct
```

Migrations must bypass the pooler. DDL relies on session state — advisory locks, `SET`,
temporary objects — and transaction pooling gives a different server connection per
transaction.

## Configuration model

Configuration is environment-driven. The `edoburu/pgbouncer` image renders both
`pgbouncer.ini` and its auth file from `DB_*` and `POOL_*` variables, and the shipped
`entrypoint.sh` maps cookiecutter-django's `POSTGRES_*` names onto them.

The harness deliberately ships **no** `pgbouncer.ini`. Version 1.x did, and the Compose
fragment never mounted it, so editing it changed nothing — a configuration file that
looks authoritative and is inert is worse than no file at all. To run a hand-written
configuration, mount it over `/etc/pgbouncer/pgbouncer.ini` and drop the custom
entrypoint.

## Tuning presets

| File | Target host |
|---|---|
| `compose/pgbouncer/postgres/tuning-small.conf` | ~2 GB shared box |
| `compose/pgbouncer/postgres/tuning-medium.conf` | ~4 GB shared box |

Keep PostgreSQL's `max_connections` low and raise PgBouncer's `max_client_conn` and
`default_pool_size` instead. That reallocation is the entire point.

## Activation checklist

1. The project has a `postgres` service (`use_docker=y`, or an equivalent of your own).
2. The overlay has been applied, so the templates are present.
3. Either `--with-pgbouncer`, or set `USE_PGBOUNCER=True`, `POSTGRES_HOST=pgbouncer`,
   `POSTGRES_PORT=6432`, `CONN_MAX_AGE=0` yourself.
4. Merge `docker-compose.pgbouncer.yml` into your Compose invocation.
5. For production, point the pgbouncer `env_file` at `./.envs/.production/.postgres`.
6. Run migrations with `--database=direct`.

The published port binds to `127.0.0.1:6432`. A pooler reachable from other interfaces is
an unauthenticated path to your database if the auth file is ever misconfigured.

## Non-goals

- Not a default. Local development without Docker stays simple.
- Not a database engine change.
- Not a replacement for query optimisation.
