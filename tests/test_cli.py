"""Tests for the command line interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_ai_harness import __version__
from django_ai_harness.cli import main


def test_info_lists_the_pins(capsys: pytest.CaptureFixture[str]):
    assert main(["info"]) == 0
    out = capsys.readouterr().out
    assert __version__ in out
    assert "cookiecutter-django" in out
    assert "ipython==" in out


def test_version_flag(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_is_an_error():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_apply_check_reports_drift(project: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["apply", str(project), "--check"]) == 1
    assert "AGENTS.md" in capsys.readouterr().out


def test_apply_then_check_is_clean(project: Path):
    assert main(["apply", str(project)]) == 0
    assert main(["apply", str(project), "--check"]) == 0


def test_apply_reports_a_non_django_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["apply", str(tmp_path)]) == 2
    assert "manage.py" in capsys.readouterr().err


def test_new_rejects_an_existing_target(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    target = tmp_path / "shop"
    target.mkdir()
    assert main(["new", str(target), "Shop"]) == 2
    assert "already exists" in capsys.readouterr().err


def test_invalid_choice_is_rejected_before_any_work(tmp_path: Path):
    with pytest.raises(SystemExit) as excinfo:
        main(["new", str(tmp_path / "shop"), "Shop", "--rest-api", "GraphQL"])
    assert excinfo.value.code == 2
