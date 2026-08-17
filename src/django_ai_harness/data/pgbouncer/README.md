# PgBouncer (opt-in)

PostgreSQL stays the database engine. PgBouncer sits in front of it as a
**transaction-mode** pooler, so a host running many workers stops paying for one
Postgres backend process per client connection.

Reach for it when connection count — not query throughput — is what hurts: many Gunicorn
or Celery workers, a small VPS, or a managed Postgres with a low connection cap. A single
worker on a laptop does not need it.

## Enable

The project must have been generated with Docker Compose (`use_docker=y`).

```bash
django-ai-harness apply . --with-pgbouncer
docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d
```

That writes the following into `.envs/*/.postgres` and `.envs/*/.django`:

```bash
USE_PGBOUNCER=True
POSTGRES_HOST=pgbouncer
POSTGRES_PORT=6432
CONN_MAX_AGE=0
POSTGRES_HOST_DIRECT=postgres
POSTGRES_PORT_DIRECT=5432
```

For production, also point the `pgbouncer` service's `env_file` at
`./.envs/.production/.postgres` and use `docker-compose.production.yml`.

## Migrations must bypass the pooler

Transaction pooling gives a different server connection per transaction, which breaks
DDL that relies on session state (advisory locks, `SET`, temporary objects). The overlay
therefore defines a second database alias that connects straight to Postgres:

```bash
python manage.py migrate --database=direct
```

`DATABASES["direct"]` carries `TEST = {"MIRROR": "default"}`, so the test runner reuses
the default test database instead of trying to create a second one.

## What the overlay changes in Django

Inside the `USE_PGBOUNCER` block of `config/settings/local.py` and `production.py`:

| Setting | Value | Why |
|---|---|---|
| `CONN_MAX_AGE` | `0` | Persistent Django connections would pin a pooled server connection |
| `DISABLE_SERVER_SIDE_CURSORS` | `True` | Server-side cursors cannot survive across transactions |
| `DATABASES["direct"]` | unpooled clone | DDL path that skips the pooler |

`ATOMIC_REQUESTS` is already enabled by cookiecutter-django and pairs well with
transaction pooling.

## Configuration model

Configuration is **environment-driven**. The `edoburu/pgbouncer` image renders both
`pgbouncer.ini` and the auth file from the variables in
`docker-compose.pgbouncer.yml`, and `entrypoint.sh` maps cookiecutter-django's
`POSTGRES_*` names onto the `DB_*` names the image expects. There is no checked-in ini
file to drift out of sync.

Tune it through Compose:

| Variable | Default | Meaning |
|---|---|---|
| `POOL_MODE` | `transaction` | Do not change without re-reading the Django notes above |
| `MAX_CLIENT_CONN` | `200` | Client connections PgBouncer accepts |
| `DEFAULT_POOL_SIZE` | `20` | Server connections per user/database pair |
| `MIN_POOL_SIZE` | `2` | Warm connections kept open |
| `RESERVE_POOL_SIZE` | `5` | Burst capacity above the default pool |

To run a hand-written configuration instead, mount your own file over
`/etc/pgbouncer/pgbouncer.ini` and remove the custom `entrypoint`.

## PostgreSQL tuning presets

Let PgBouncer absorb client concurrency and keep `max_connections` low on Postgres:

```yaml
# in the postgres service
volumes:
  - ./compose/pgbouncer/postgres/tuning-small.conf:/etc/postgresql/conf.d/harness-tuning.conf:ro
```

| Preset | Target host |
|---|---|
| `postgres/tuning-small.conf` | ~2 GB shared VPS |
| `postgres/tuning-medium.conf` | ~4 GB shared VPS |

## Files

| Path | Role |
|---|---|
| `docker-compose.pgbouncer.yml` | Compose merge fragment, at the project root |
| `compose/pgbouncer/entrypoint.sh` | Maps `POSTGRES_*` onto the image's `DB_*` |
| `compose/pgbouncer/postgres/*.conf` | Optional PostgreSQL tuning presets |

The published port is bound to `127.0.0.1:6432`, never to all interfaces.

Background and trade-offs: `knowledge/dx-practices/postgres-pooling.md` in the harness.
