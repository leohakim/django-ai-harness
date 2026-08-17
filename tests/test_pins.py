"""Tests for the pinned upstream references."""

from __future__ import annotations

import re

import pytest

from django_ai_harness.pins import cookiecutter_ref
from django_ai_harness.pins import data_path
from django_ai_harness.pins import dev_requirements
from django_ai_harness.pins import normalize_name


def test_cookiecutter_ref_is_an_immutable_commit(monkeypatch: pytest.MonkeyPatch):
    """A branch name here would silently change what every user generates."""
    monkeypatch.delenv("COOKIECUTTER_DJANGO_REF", raising=False)
    assert re.fullmatch(r"[0-9a-f]{40}", cookiecutter_ref())


def test_environment_overrides_the_pin(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COOKIECUTTER_DJANGO_REF", "master")
    assert cookiecutter_ref() == "master"


@pytest.mark.parametrize(
    ("requirement", "expected"),
    [
        ("django-stubs[compatible-mypy]==6.0.9", "django-stubs"),
        ("psycopg[c]==3.3.4", "psycopg"),
        ("Django_Rich==2.2.0", "django-rich"),
        ("ipython", "ipython"),
    ],
)
def test_normalize_name(requirement: str, expected: str):
    assert normalize_name(requirement) == expected


def test_dev_requirements_are_sorted_and_pinned():
    requirements = dev_requirements()
    assert requirements
    assert [r.name for r in requirements] == sorted(r.name for r in requirements)
    assert all("==" in r for r in requirements)


def test_packaged_data_is_present():
    assert data_path("cookiecutter-django.pin").is_file()
    assert data_path("dev-requirements.txt").is_file()
    assert (data_path("pgbouncer") / "docker-compose.pgbouncer.yml").is_file()
    assert (data_path("pgbouncer") / "docker-compose.pgbouncer.production.yml").is_file()
    assert (data_path("pgbouncer") / "entrypoint.sh").is_file()


def test_dead_config_files_are_not_shipped():
    """pgbouncer.ini and userlist.txt were never mounted by the Compose fragment."""
    pgbouncer = data_path("pgbouncer")
    assert not (pgbouncer / "pgbouncer.ini").exists()
    assert not (pgbouncer / "userlist.txt.example").exists()
