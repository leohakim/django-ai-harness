#!/bin/sh
# Map cookiecutter-django POSTGRES_* env files into edoburu/pgbouncer DB_* vars.
set -eu

export DB_HOST="${DB_HOST:-postgres}"
export DB_PORT="${DB_PORT:-5432}"
export DB_USER="${DB_USER:-${POSTGRES_USER}}"
export DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD}}"
export DB_NAME="${DB_NAME:-${POSTGRES_DB}}"

export POOL_MODE="${POOL_MODE:-transaction}"
export MAX_CLIENT_CONN="${MAX_CLIENT_CONN:-200}"
export DEFAULT_POOL_SIZE="${DEFAULT_POOL_SIZE:-20}"
export MIN_POOL_SIZE="${MIN_POOL_SIZE:-2}"
export RESERVE_POOL_SIZE="${RESERVE_POOL_SIZE:-5}"
export AUTH_TYPE="${AUTH_TYPE:-scram-sha-256}"

if [ -z "${DB_USER}" ] || [ -z "${DB_PASSWORD}" ] || [ -z "${DB_NAME}" ]; then
  echo "error: need POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB (or DB_*) for PgBouncer" >&2
  exit 1
fi

exec /usr/local/bin/entrypoint.sh
