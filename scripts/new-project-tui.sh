#!/usr/bin/env bash
# Guided Textual wizard from a source checkout of django-ai-harness.
#
# Installed users should prefer:
#   uvx --from 'django-ai-harness[wizard]' django-ai-harness wizard
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v uv >/dev/null || { echo "error: uv is required — https://docs.astral.sh/uv/" >&2; exit 1; }

exec uv run --project "${HARNESS_ROOT}" --extra wizard django-ai-harness wizard "$@"
