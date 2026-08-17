#!/bin/sh
# Map cookiecutter-django's POSTGRES_* env file onto the DB_* variables the
# edoburu/pgbouncer image expects, then hand over to the image's own entrypoint.
#
# `set -u` would abort on an unset POSTGRES_* before the friendly check below could
# run, so every lookup carries an explicit empty default.
set -eu

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-${POSTGRES_USER:-}}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"
DB_NAME="${DB_NAME:-${POSTGRES_DB:-}}"

missing=""
[ -n "${DB_USER}" ] || missing="${missing} POSTGRES_USER"
[ -n "${DB_PASSWORD}" ] || missing="${missing} POSTGRES_PASSWORD"
[ -n "${DB_NAME}" ] || missing="${missing} POSTGRES_DB"

if [ -n "${missing}" ]; then
  echo "error: pgbouncer is missing required credentials:${missing}" >&2
  echo "hint: check the env_file of the pgbouncer service in docker-compose.pgbouncer.yml" >&2
  exit 1
fi

export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME
export POOL_MODE="${POOL_MODE:-transaction}"
export MAX_CLIENT_CONN="${MAX_CLIENT_CONN:-200}"
export DEFAULT_POOL_SIZE="${DEFAULT_POOL_SIZE:-20}"
export MIN_POOL_SIZE="${MIN_POOL_SIZE:-2}"
export RESERVE_POOL_SIZE="${RESERVE_POOL_SIZE:-5}"
export AUTH_TYPE="${AUTH_TYPE:-scram-sha-256}"
# Django sends these on connect; PgBouncer must not reject them in transaction mode.
export IGNORE_STARTUP_PARAMETERS="${IGNORE_STARTUP_PARAMETERS:-extra_float_digits,options}"

exec /usr/local/bin/entrypoint.sh "$@"
