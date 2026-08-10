#!/usr/bin/env bash
# Guided Textual TUI for creating a django-ai-harness project.
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v uv >/dev/null || { echo "error: uv not found"; exit 1; }
command -v cookiecutter >/dev/null || { echo "error: cookiecutter not found"; exit 1; }

cd "${HARNESS_ROOT}"
exec uv run --with textual python "${HARNESS_ROOT}/scripts/wizard/app.py"
