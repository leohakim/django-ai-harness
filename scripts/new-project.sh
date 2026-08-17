#!/usr/bin/env bash
# Create a new Django project from a source checkout of django-ai-harness.
#
# Installed users should prefer the published command, which needs no clone:
#   uvx django-ai-harness new ~/Projects/my_shop "My Shop"
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  cat >&2 <<'USAGE'
Usage: ./scripts/new-project.sh <target_directory> [project_name] [extra flags...]

Examples:
  ./scripts/new-project.sh ~/Projects/my_shop "My Shop"
  ./scripts/new-project.sh ~/Projects/my_shop "My Shop" --with-pgbouncer
  ./scripts/new-project.sh ~/Projects/my_api "My API" --use-celery y --use-docker n

Guided alternative:
  ./scripts/new-project-tui.sh
USAGE
  exit 1
fi

command -v uv >/dev/null || { echo "error: uv is required — https://docs.astral.sh/uv/" >&2; exit 1; }

exec uv run --project "${HARNESS_ROOT}" django-ai-harness new "$@"
