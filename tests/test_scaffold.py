"""Tests for project configuration and the cookiecutter context."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_ai_harness.scaffold import ProjectConfig
from django_ai_harness.scaffold import ScaffoldError
from django_ai_harness.scaffold import next_steps
from django_ai_harness.scaffold import sanitize_slug
from django_ai_harness.scaffold import scaffold


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("my_shop", "my_shop"),
        ("my-shop", "my_shop"),
        ("My Shop", "My_Shop"),
        ("my.shop", "my_shop"),
        ("2fast", "p_2fast"),
        ("my shop!!", "my_shop"),
    ],
)
def test_sanitize_slug(raw: str, expected: str):
    assert sanitize_slug(raw) == expected


@pytest.mark.parametrize("raw", ["", "!!!", "test", "django", "config"])
def test_sanitize_slug_rejects_unusable_names(raw: str):
    with pytest.raises(ValueError, match=r"empty|usable"):
        sanitize_slug(raw)


def test_slug_is_derived_from_the_target_directory(tmp_path: Path):
    config = ProjectConfig(target=tmp_path / "my-shop", project_name="My Shop")
    assert config.project_slug == "my_shop"


def test_pgbouncer_forces_docker(tmp_path: Path):
    config = ProjectConfig(
        target=tmp_path / "shop",
        project_name="Shop",
        use_docker="n",
        with_pgbouncer=True,
    )
    assert config.use_docker == "y"


def test_email_defaults_to_the_domain(tmp_path: Path):
    config = ProjectConfig(target=tmp_path / "shop", project_name="Shop", domain_name="acme.dev")
    assert config.email == "hello@acme.dev"


def test_context_carries_every_cookiecutter_key(tmp_path: Path):
    context = ProjectConfig(target=tmp_path / "shop", project_name="Shop").as_cookiecutter_context()

    assert context["project_slug"] == "shop"
    assert context["keep_local_envs_in_vcs"] == "n"
    assert context["debug"] == "n"
    assert set(context) >= {"project_name", "use_docker", "rest_api", "ci_tool", "timezone"}


def test_context_accepts_characters_that_broke_cli_parsing(tmp_path: Path):
    """v1 shelled out with `key=value`, so an `=` in a description had to be rejected."""
    config = ProjectConfig(
        target=tmp_path / "shop",
        project_name="Shop",
        description="Sales = revenue, obviously",
    )
    assert config.as_cookiecutter_context()["description"] == "Sales = revenue, obviously"


def test_control_characters_are_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="control character"):
        ProjectConfig(target=tmp_path / "shop", project_name="Shop\x00injected")


def test_scaffold_refuses_to_overwrite_an_existing_target(tmp_path: Path):
    target = tmp_path / "shop"
    target.mkdir()
    config = ProjectConfig(target=target, project_name="Shop")

    with pytest.raises(ScaffoldError, match="already exists"):
        scaffold(config)


def test_next_steps_uses_the_direct_alias_for_pooled_projects(tmp_path: Path):
    config = ProjectConfig(target=tmp_path / "shop", project_name="Shop", with_pgbouncer=True)
    assert "migrate --database=direct" in next_steps(config)


def test_next_steps_are_localized(tmp_path: Path):
    config = ProjectConfig(
        target=tmp_path / "shop",
        project_name="Shop",
        use_docker="n",
        language="es",
    )
    assert "Proyecto listo en" in next_steps(config)
