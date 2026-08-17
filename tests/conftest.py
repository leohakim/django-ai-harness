"""Shared fixtures.

The overlay is exercised against a synthetic tree that mirrors the parts of a
cookiecutter-django project it actually touches. Building it in code rather than
checking in a fixture keeps the tests fast, hermetic and readable: every file present is
a file some assertion depends on.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PYPROJECT = """\
[project]
name = "acme"
version = "0.1.0"
requires-python = "==3.14.*"
dependencies = [
  "django==6.0.8",
]

[dependency-groups]
dev = [
  "coverage==7.15.4",
  "django-debug-toolbar==7.0.0",
  "factory-boy==3.3.3",
  "ipdb==0.13.13",
  "pytest==9.1.1",
  "ruff==0.16.2",
  "sphinx==9.1.0",
  "sphinx-autobuild==2025.8.25",
]

[tool.ruff]
line-length = 119
"""

BASE_SETTINGS = '''\
"""Base settings."""

import environ

env = environ.Env()

DJANGO_APPS = ["django.contrib.admin"]
LOCAL_APPS = ["acme.users"]
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

DATABASES = {"default": env.db("DATABASE_URL", default="postgres:///acme")}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}
'''

LOCAL_SETTINGS = '''\
"""Local settings."""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import env

DEBUG = True

INSTALLED_APPS += ["django_extensions"]

# Your stuff...
'''

PRODUCTION_SETTINGS = '''\
"""Production settings."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
'''

URLS = """\
from django.conf import settings
from django.urls import include
from django.urls import path

urlpatterns = [path("", include("acme.users.urls"))]
"""


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A minimal tree shaped like a cookiecutter-django project."""
    root = tmp_path / "acme"
    files = {
        "manage.py": "#!/usr/bin/env python\n",
        "pyproject.toml": PYPROJECT,
        ".python-version": "3.14\n",
        "config/__init__.py": "",
        "config/urls.py": URLS,
        "config/settings/__init__.py": "",
        "config/settings/base.py": BASE_SETTINGS,
        "config/settings/local.py": LOCAL_SETTINGS,
        "config/settings/production.py": PRODUCTION_SETTINGS,
        "config/settings/test.py": "from .base import *  # noqa: F403\n",
        "acme/__init__.py": "",
        "acme/conftest.py": "",
        "acme/users/__init__.py": "",
        "acme/users/models.py": "",
        "acme/users/migrations/__init__.py": "",
        "acme/users/migrations/0001_initial.py": "",
        "acme/users/migrations/0002_alter_user.py": "",
        ".envs/.local/.postgres": (
            "POSTGRES_HOST=postgres\nPOSTGRES_PORT=5432\nPOSTGRES_DB=acme\n"
        ),
        ".envs/.local/.django": "USE_DOCKER=yes\n",
        ".envs/.production/.postgres": "POSTGRES_HOST=postgres\nPOSTGRES_PORT=5432\n",
        ".envs/.production/.django": "DJANGO_SETTINGS_MODULE=config.settings.production\n",
    }
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


def tree_snapshot(root: Path) -> dict[str, str]:
    """Map every file under ``root`` to its content, for idempotency assertions."""
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
