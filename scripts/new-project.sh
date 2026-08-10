#!/usr/bin/env bash
# Create a new Django project: cookiecutter-django (pinned ref) + django-ai-harness overlay.
# For a guided experience, prefer: ./scripts/new-project-tui.sh
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"
PROJECT_NAME="${2:-New Django App}"

if [[ -z "${TARGET}" ]]; then
  echo "Usage: $0 <target_directory> [project_name]"
  echo "Example: $0 ~/Projects/my_shop \"My Shop\""
  echo
  echo "Tip: for a guided TUI wizard run:"
  echo "  ./scripts/new-project-tui.sh"
  exit 1
fi

export COOKIECUTTER_DJANGO_REF="${COOKIECUTTER_DJANGO_REF:-cdbe7265c79f43fd3e22c4527a97c8c7a5c72a5b}"
USE_DOCKER="${USE_DOCKER:-y}"
WITH_PGBOUNCER_FLAG=0
if [[ "${WITH_PGBOUNCER:-0}" == "1" || "${WITH_PGBOUNCER:-}" == "y" || "${WITH_PGBOUNCER:-}" == "yes" ]]; then
  WITH_PGBOUNCER_FLAG=1
  USE_DOCKER="y"
fi

cd "${HARNESS_ROOT}"
ARGS=(
  --target "${TARGET}"
  --project-name "${PROJECT_NAME}"
  --use-docker "${USE_DOCKER}"
  --rest-api "${REST_API:-DRF}"
  --use-celery "${USE_CELERY:-n}"
  --frontend-pipeline "${FRONTEND_PIPELINE:-None}"
  --ci-tool "${CI_TOOL:-Github}"
  --use-whitenoise "${USE_WHITENOISE:-y}"
  --use-sentry "${USE_SENTRY:-n}"
  --cloud-provider "${CLOUD_PROVIDER:-None}"
)
if [[ "${WITH_PGBOUNCER_FLAG}" == "1" ]]; then
  ARGS+=(--with-pgbouncer)
fi

exec uv run python "${HARNESS_ROOT}/scripts/lib/cli_scaffold.py" "${ARGS[@]}"
