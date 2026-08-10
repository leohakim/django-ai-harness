#!/usr/bin/env python3
"""Apply django-ai-harness overlay onto a cookiecutter-django project (idempotent)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

OVERLAY_VERSION = "1.0.0"
MARKER_BEGIN = "# >>> django-ai-harness"
MARKER_END = "# <<< django-ai-harness"
HTML_MARKER_BEGIN = "<!-- >>> django-ai-harness -->"
HTML_MARKER_END = "<!-- <<< django-ai-harness -->"

DEV_DEPS = [
    "ipython",
    "django-browser-reload",
    "django-rich",
    "django-read-only",
    "django-linear-migrations",
    "django-version-checks",
]


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def find_project_package(project_root: Path) -> str:
    """Detect nested Django project package (cookiecutter two-tier layout)."""
    manage = project_root / "manage.py"
    if not manage.exists():
        die(f"manage.py not found in {project_root}")
    text = manage.read_text(encoding="utf-8")
    m = re.search(r"DJANGO_SETTINGS_MODULE['\"]?\s*,\s*['\"]([^'\"]+)['\"]", text)
    if not m:
        # fallback: look for config.settings
        if (project_root / "config" / "settings").exists():
            # find first dir that is not config/docs/tests/utility with apps.py or users/
            for child in project_root.iterdir():
                if child.is_dir() and child.name not in {
                    ".git",
                    ".github",
                    ".venv",
                    "config",
                    "docs",
                    "tests",
                    "utility",
                    "locale",
                    "node_modules",
                    ".envs",
                    "harness_templates",
                }:
                    if (child / "users").exists() or (child / "conftest.py").exists():
                        return child.name
        die("Could not detect project package name")
    module = m.group(1)  # e.g. config.settings.local — not helpful
    # Prefer directory containing users app
    for child in project_root.iterdir():
        if child.is_dir() and (child / "users").is_dir():
            return child.name
    die("Could not find project package directory containing users/")


def upsert_marked_block(path: Path, begin: str, end: str, body: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    block = f"{begin}\n{body.rstrip()}\n{end}\n"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if begin in text and end in text:
            pattern = re.compile(
                re.escape(begin) + r".*?" + re.escape(end) + r"\n?",
                re.DOTALL,
            )
            new_text, n = pattern.subn(block, text, count=1)
            if n:
                if new_text != text:
                    path.write_text(new_text, encoding="utf-8")
                    return True
                return False
        # append
        if not text.endswith("\n"):
            text += "\n"
        path.write_text(text + "\n" + block, encoding="utf-8")
        return True
    path.write_text(block, encoding="utf-8")
    return True


def write_file(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def ensure_dev_deps(project_root: Path) -> None:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        die("pyproject.toml missing — is this cookiecutter-django?")
    text = pyproject.read_text(encoding="utf-8")
    missing = [dep for dep in DEV_DEPS if dep.replace("_", "-") not in text and dep not in text]
    # also check hyphen/underscore variants already present loosely
    really_missing = []
    for dep in DEV_DEPS:
        if dep not in text and dep.replace("-", "_") not in text:
            really_missing.append(dep)
    if not really_missing:
        print("dev deps already present")
        return
    print(f"adding dev deps with uv: {', '.join(really_missing)}")
    cmd = ["uv", "add", "--group", "dev", *really_missing]
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
    except FileNotFoundError:
        die("uv not found on PATH")
    except subprocess.CalledProcessError as exc:
        die(f"uv add failed: {exc}")


def patch_local_settings(project_root: Path) -> bool:
    path = project_root / "config" / "settings" / "local.py"
    if not path.exists():
        die("config/settings/local.py missing")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    py_file = project_root / ".python-version"
    if py_file.exists():
        parts = py_file.read_text(encoding="utf-8").strip().split(".")
        if len(parts) >= 2:
            py_ver = f"{parts[0]}.{parts[1]}"
    body = f"""# Extra DX from django-ai-harness (safe for local only)
INSTALLED_APPS += ["django_browser_reload", "django_linear_migrations"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# django-read-only: protect against accidental writes in shells when enabled
# Toggle with: import django_read_only; django_read_only.enable()
INSTALLED_APPS += ["django_read_only"]

# django-version-checks: keep environments aligned
INSTALLED_APPS += ["django_version_checks"]
VERSION_CHECKS = {{
    "python": "~={py_ver}.0",
}}

# Prefer IPython when available (django-extensions shell_plus)
SHELL_PLUS = "ipython"
"""
    return upsert_marked_block(path, MARKER_BEGIN, MARKER_END, body)


def patch_urls(project_root: Path) -> bool:
    path = project_root / "config" / "urls.py"
    if not path.exists():
        return False
    body = '''if settings.DEBUG:
    try:
        urlpatterns += [
            path("__reload__/", include("django_browser_reload.urls")),
        ]
    except Exception:  # pragma: no cover - defensive for partial installs
        pass
'''
    return upsert_marked_block(path, MARKER_BEGIN, MARKER_END, body)


def patch_base_settings_notes(project_root: Path) -> bool:
    path = project_root / "config" / "settings" / "base.py"
    if not path.exists():
        return False
    body = '''# Settings hygiene (django-ai-harness):
# - Import django.conf.settings from app code, never this module directly.
# - Do not mutate settings at runtime in request/business code.
# - Keep secrets and environment-specific values in env vars / local.py / production.py.
'''
    return upsert_marked_block(path, MARKER_BEGIN, MARKER_END, body)


def add_seed_command(project_root: Path, package: str) -> bool:
    base = project_root / package / "management" / "commands"
    init1 = project_root / package / "management" / "__init__.py"
    init2 = base / "__init__.py"
    changed = False
    for init in (init1, init2):
        if write_file(init, ""):
            changed = True
    cmd = base / "seed_database.py"
    content = '''"""Seed local/dev database with Factory Boy (customize per project)."""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed the database with development data."

    @transaction.atomic
    def handle(self, *args, **options):
        # Example: create a couple of users if factories exist.
        try:
            from {package}.users.tests.factories import UserFactory
        except Exception as exc:  # pragma: no cover
            self.stderr.write(self.style.ERROR(f"Could not import UserFactory: {{exc}}"))
            self.stdout.write(
                "Add factories and extend this command as your domain grows."
            )
            return

        users = UserFactory.create_batch(3)
        self.stdout.write(self.style.SUCCESS(f"Created {{len(users)}} users"))
'''.format(package=package)
    if write_file(cmd, content):
        changed = True
    return changed


def add_pending_migrations_test(project_root: Path, package: str) -> bool:
    path = project_root / package / "tests" / "test_pending_migrations.py"
    content = '''import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_no_pending_migrations():
    """Fail if model changes are missing migrations."""
    try:
        call_command("makemigrations", check=True, dry_run=True)
    except SystemExit as exc:  # Django may exit non-zero
        if exc.code not in (None, 0):
            raise AssertionError("Pending migrations detected") from exc
'''
    # Ensure tests package exists
    tests_init = project_root / package / "tests" / "__init__.py"
    write_file(tests_init, "")
    return write_file(path, content)


def add_agents_md(project_root: Path, harness_root: Path) -> bool:
    content = '''# AGENTS.md

This project was bootstrapped with **cookiecutter-django** and **django-ai-harness**.

## Architecture (HackSoft)

- Business writes/workflows → `services.py` (or `services/`)
- Business reads/queries → `selectors.py` (or `selectors/`)
- HTTP layer stays thin (DRF APIs / views call services & selectors)
- Do not put domain rules in serializers, signals, or `Model.save`

See harness knowledge: `knowledge/architecture/hacksoft.md` in the django-ai-harness repo.

## DX

- Use `uv run` for commands
- Keep Ruff + pre-commit green
- Prefer `seed_database` + Factory Boy for local data
- Re-apply overlay after harness upgrades

## Skills

If Cursor skills from django-ai-harness are available, use:

- `django-hacksoft` for feature work
- `django-dx-review` before PRs
'''
    return write_file(project_root / "AGENTS.md", content)


def add_project_doc(project_root: Path) -> bool:
    content = '''# django-ai-harness notes

This project includes the django-ai-harness overlay.

- Re-apply: `python /path/to/django-ai-harness/overlay/apply.py .`
- Docs: https://github.com/leohakim/django-ai-harness
'''
    return write_file(project_root / "docs" / "django-ai-harness.md", content)


def add_app_skeleton(project_root: Path) -> bool:
    root = project_root / "harness_templates" / "app_skeleton"
    files = {
        "services.py": '''"""Write-side business logic lives here."""

from __future__ import annotations

from django.db import transaction


@transaction.atomic
def example_create(*, name: str) -> None:
    """Replace with real domain services (keyword-only args, full_clean, etc.)."""
    raise NotImplementedError
''',
        "selectors.py": '''"""Read-side queries live here. No state mutations."""

from __future__ import annotations


def example_list():
    raise NotImplementedError
''',
        "apis/__init__.py": "",
        "apis/example.py": '''"""Thin API example — validate, call service/selector, serialize."""

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ExampleCreateApi(APIView):
    def post(self, request: Request) -> Response:
        # validate with InputSerializer, call services.example_create, return OutputSerializer
        return Response({"detail": "not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)
''',
        "README.md": '''# App skeleton (HackSoft)

Copy `services.py`, `selectors.py`, and `apis/` patterns into new apps.
Tests should mirror layers under `tests/services`, `tests/selectors`, `tests/apis`.
''',
    }
    changed = False
    for rel, content in files.items():
        if write_file(root / rel, content):
            changed = True
    return changed


def write_marker(project_root: Path) -> None:
    data = {
        "overlay_version": OVERLAY_VERSION,
        "harness": "django-ai-harness",
    }
    path = project_root / ".django-ai-harness.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ensure_linear_migration_files(project_root: Path) -> bool:
    """Create max_migration.txt files required by django-linear-migrations."""
    changed = False
    for migrations_dir in project_root.rglob("migrations"):
        if not migrations_dir.is_dir():
            continue
        if migrations_dir.name != "migrations":
            continue
        # skip virtualenvs
        if ".venv" in migrations_dir.parts or "site-packages" in migrations_dir.parts:
            continue
        init = migrations_dir / "__init__.py"
        if not init.exists():
            continue
        migration_modules = sorted(
            p.name
            for p in migrations_dir.glob("*.py")
            if p.name != "__init__.py" and not p.name.startswith("__")
        )
        if not migration_modules:
            continue
        latest = migration_modules[-1].removesuffix(".py")
        target = migrations_dir / "max_migration.txt"
        content = latest + "\n"
        if target.exists() and target.read_text(encoding="utf-8") == content:
            continue
        target.write_text(content, encoding="utf-8")
        changed = True
    return changed


def apply(project_root: Path, harness_root: Path) -> None:
    project_root = project_root.resolve()
    harness_root = harness_root.resolve()
    print(f"Applying overlay v{OVERLAY_VERSION} to {project_root}")
    package = find_project_package(project_root)
    print(f"Detected project package: {package}")

    ensure_dev_deps(project_root)
    changes = [
        ("AGENTS.md", add_agents_md(project_root, harness_root)),
        ("local settings", patch_local_settings(project_root)),
        ("urls", patch_urls(project_root)),
        ("base settings notes", patch_base_settings_notes(project_root)),
        ("seed_database", add_seed_command(project_root, package)),
        ("pending migrations test", add_pending_migrations_test(project_root, package)),
        ("project doc", add_project_doc(project_root)),
        ("app skeleton", add_app_skeleton(project_root)),
        ("linear migration files", ensure_linear_migration_files(project_root)),
    ]
    write_marker(project_root)
    for label, changed in changes:
        print(f" - {label}: {'updated' if changed else 'unchanged'}")
    print("Done. Next: `uv sync` && `uv run python manage.py check`")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--harness-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to django-ai-harness checkout",
    )
    args = parser.parse_args()
    apply(args.project_root, args.harness_root)


if __name__ == "__main__":
    main()
