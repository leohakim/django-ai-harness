#!/usr/bin/env bash
# Create a new Django project: cookiecutter-django (pinned ref) + django-ai-harness overlay.
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"
PROJECT_NAME="${2:-New Django App}"
# Pin for supply-chain stability; override with COOKIECUTTER_DJANGO_REF=master to track latest.
COOKIECUTTER_DJANGO_REF="${COOKIECUTTER_DJANGO_REF:-cdbe7265c79f43fd3e22c4527a97c8c7a5c72a5b}"

if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 <target_directory> [project_name]"
  echo "Example: $0 ~/Projects/my_shop \"My Shop\""
  exit 1
fi

if [[ -e "${TARGET}" ]]; then
  echo "error: target already exists: ${TARGET}"
  exit 1
fi

command -v cookiecutter >/dev/null || { echo "error: cookiecutter not found"; exit 1; }
command -v uv >/dev/null || { echo "error: uv not found"; exit 1; }

PARENT="$(dirname "${TARGET}")"
RAW_SLUG="$(basename "${TARGET}")"
# cookiecutter-django requires a valid Python identifier
SLUG="${RAW_SLUG//-/_}"
SLUG="${SLUG//./_}"

# PgBouncer needs Compose postgres; force Docker when opted in.
# Default Docker on so the documented migrate path works out of the box.
USE_DOCKER="${USE_DOCKER:-y}"
WITH_PGBOUNCER_FLAG=0
if [[ "${WITH_PGBOUNCER:-0}" == "1" || "${WITH_PGBOUNCER:-}" == "y" || "${WITH_PGBOUNCER:-}" == "yes" ]]; then
  WITH_PGBOUNCER_FLAG=1
  if [[ "${USE_DOCKER}" != "y" ]]; then
    echo "==> WITH_PGBOUNCER=1 requires Docker Compose; setting USE_DOCKER=y"
    USE_DOCKER="y"
  fi
fi

mkdir -p "${PARENT}"
TMP="$(mktemp -d)"
cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

echo "==> Generating cookiecutter-django @ ${COOKIECUTTER_DJANGO_REF}"
cookiecutter "gh:cookiecutter/cookiecutter-django" --checkout "${COOKIECUTTER_DJANGO_REF}" --no-input --output-dir "${TMP}" \
  project_name="${PROJECT_NAME}" \
  project_slug="${SLUG}" \
  description="Project managed with django-ai-harness" \
  author_name="${AUTHOR_NAME:-django-ai-harness}" \
  domain_name="${DOMAIN_NAME:-example.com}" \
  email="${EMAIL:-maintainers@example.com}" \
  open_source_license="MIT" \
  username_type="email" \
  timezone="UTC" \
  windows="n" \
  editor="None" \
  use_docker="${USE_DOCKER}" \
  cloud_provider="None" \
  mail_service="Other SMTP" \
  rest_api="DRF" \
  use_async="n" \
  frontend_pipeline="None" \
  use_celery="n" \
  mail_catcher="None" \
  use_sentry="n" \
  use_whitenoise="y" \
  use_heroku="n" \
  ci_tool="Github" \
  keep_local_envs_in_vcs="y" \
  debug="n"

GENERATED="${TMP}/${SLUG}"
if [[ ! -d "${GENERATED}" ]]; then
  GENERATED="$(find "${TMP}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
fi

echo "==> Applying django-ai-harness overlay"
OVERLAY_ARGS=("${GENERATED}" --harness-root "${HARNESS_ROOT}")
if [[ "${WITH_PGBOUNCER_FLAG}" == "1" ]]; then
  OVERLAY_ARGS+=(--with-pgbouncer)
fi
python3 "${HARNESS_ROOT}/overlay/apply.py" "${OVERLAY_ARGS[@]}"

echo "==> Moving to ${TARGET}"
# Generated folder uses sanitized slug; move to the user-requested path
mv "${GENERATED}" "${TARGET}"

if [[ "${WITH_PGBOUNCER_FLAG}" == "1" ]]; then
  NEXT_COMPOSE=$'  docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d\n  # migrate bypasses the pooler:\n  POSTGRES_HOST=postgres POSTGRES_PORT=5432 USE_PGBOUNCER=False uv run python manage.py migrate'
else
  NEXT_COMPOSE=$'  # If Docker was enabled:\n  # docker compose -f docker-compose.local.yml up -d\n  uv run python manage.py migrate'
fi

cat <<EOF

Project ready at: ${TARGET}

Next:
  cd ${TARGET}
  uv sync
${NEXT_COMPOSE}
  uv run python manage.py runserver

Read: ${HARNESS_ROOT}/docs/getting-started.md
$([ "${WITH_PGBOUNCER_FLAG}" = "1" ] && echo "PgBouncer: ${HARNESS_ROOT}/knowledge/dx-practices/postgres-pooling.md")
EOF
