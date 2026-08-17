"""Tests for the overlay.

These cover the three properties the overlay promises: it is idempotent, it is
deterministic (no network, no resolver), and it upgrades managed files without ever
clobbering a local edit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import tree_snapshot

from django_ai_harness import OVERLAY_VERSION
from django_ai_harness.overlay import SKIPPED_LEGACY
from django_ai_harness.overlay import SKIPPED_LOCAL
from django_ai_harness.overlay import STATE_FILENAME
from django_ai_harness.overlay import UPDATED
from django_ai_harness.overlay import OverlayError
from django_ai_harness.overlay import apply
from django_ai_harness.overlay import find_project_package
from django_ai_harness.overlay import merge_dev_requirements
from django_ai_harness.overlay import migrate_legacy_markers
from django_ai_harness.overlay import upsert_marked_block
from django_ai_harness.pins import Requirement
from django_ai_harness.pins import dev_requirements


def read_state(project: Path) -> dict:
    return json.loads((project / STATE_FILENAME).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Marker blocks
# ---------------------------------------------------------------------------


def test_upsert_inserts_then_replaces_in_place():
    text = upsert_marked_block("x = 1\n", "local", "y = 2")
    assert text.count("# >>> django-ai-harness:local") == 1

    again = upsert_marked_block(text, "local", "y = 3")
    assert again.count("# >>> django-ai-harness:local") == 1
    assert "y = 3" in again
    assert "y = 2" not in again


def test_upsert_is_stable_when_body_is_unchanged():
    once = upsert_marked_block("x = 1\n", "local", "y = 2")
    assert upsert_marked_block(once, "local", "y = 2") == once


def test_marker_names_never_collide_by_prefix():
    """Regression: ``:local`` must not swallow the longer ``:pgbouncer`` block.

    Overlay 1.x used a bare ``# >>> django-ai-harness`` marker that was a prefix of every
    namespaced marker, so an unanchored regex could match the opening of one block and
    the closing of another, corrupting the settings file.
    """
    text = upsert_marked_block("BASE = 1\n", "pgbouncer", "POOLED = True")
    text = upsert_marked_block(text, "local", "DEBUG = True")

    text = upsert_marked_block(text, "local", "DEBUG = False")

    assert "POOLED = True" in text
    assert "DEBUG = False" in text
    assert text.count("# >>> django-ai-harness:pgbouncer") == 1
    assert text.count("# <<< django-ai-harness:pgbouncer") == 1
    assert ":pgbouncer\n" in text  # no dangling suffix left behind


def test_legacy_bare_markers_are_migrated_not_duplicated():
    legacy = "A = 1\n\n# >>> django-ai-harness\nOLD = True\n# <<< django-ai-harness\n"
    migrated = migrate_legacy_markers(legacy, "local")
    assert "# >>> django-ai-harness:local" in migrated

    updated = upsert_marked_block(migrated, "local", "NEW = True")
    assert updated.count("# >>> django-ai-harness:local") == 1
    assert "OLD = True" not in updated


def test_legacy_migration_leaves_namespaced_markers_alone():
    text = upsert_marked_block("A = 1\n", "pgbouncer", "POOLED = True")
    assert migrate_legacy_markers(text, "local") == text


# ---------------------------------------------------------------------------
# Dependency merging
# ---------------------------------------------------------------------------


def test_dev_requirements_are_all_pinned():
    """`>=` here is what made regeneration non-reproducible in v1."""
    for requirement in dev_requirements():
        assert "==" in requirement, f"{requirement} must be pinned with =="
        assert ">=" not in requirement


def test_merge_replaces_existing_entry_instead_of_duplicating():
    source = '[dependency-groups]\ndev = [\n  "ruff==0.1.0",\n]\n'
    merged = merge_dev_requirements(source, [Requirement("ruff==0.16.2")])
    assert merged.count('"ruff==') == 1
    assert "ruff==0.16.2" in merged


def test_merge_sorts_by_project_name_not_raw_string():
    source = (
        '[dependency-groups]\ndev = [\n  "sphinx==9.1.0",\n  "sphinx-autobuild==2025.8.25",\n]\n'
    )
    merged = merge_dev_requirements(source, [])
    assert merged.index('"sphinx==') < merged.index('"sphinx-autobuild==')


def test_merge_is_idempotent():
    source = '[dependency-groups]\ndev = [\n  "ruff==0.16.2",\n]\n'
    once = merge_dev_requirements(source, dev_requirements())
    assert merge_dev_requirements(once, dev_requirements()) == once


def test_merge_creates_the_group_when_absent():
    merged = merge_dev_requirements('[project]\nname = "x"\n', [Requirement("ruff==0.16.2")])
    assert "[dependency-groups]" in merged
    assert '"ruff==0.16.2"' in merged


# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------


def test_find_project_package(project: Path):
    assert find_project_package(project) == "acme"


def test_find_project_package_rejects_a_non_django_tree(tmp_path: Path):
    with pytest.raises(OverlayError, match=r"manage\.py"):
        find_project_package(tmp_path)


# ---------------------------------------------------------------------------
# Applying
# ---------------------------------------------------------------------------


def test_apply_writes_the_expected_artifacts(project: Path):
    apply(project)

    assert (project / "AGENTS.md").exists()
    assert (project / "docs/django-ai-harness.md").exists()
    assert (project / "harness_templates/app_skeleton/services.py").exists()
    assert (project / "acme/users/management/commands/seed_database.py").exists()
    assert (project / "acme/tests/test_pending_migrations.py").exists()
    assert (project / "docker-compose.pgbouncer.yml").exists()
    assert (project / "compose/pgbouncer/entrypoint.sh").exists()

    state = read_state(project)
    assert state["overlay_version"] == OVERLAY_VERSION
    assert state["features"]["pgbouncer"] is False
    assert "AGENTS.md" in state["managed_files"]


def test_apply_is_idempotent(project: Path):
    apply(project)
    first = tree_snapshot(project)

    result = apply(project)

    assert tree_snapshot(project) == first
    assert not result.changed


def test_apply_does_not_touch_the_network(project: Path, monkeypatch: pytest.MonkeyPatch):
    """The v1 overlay shelled out to `uv add`, which re-resolved against PyPI."""
    import subprocess  # noqa: PLC0415

    def explode(*args, **kwargs):  # noqa: ARG001
        pytest.fail("the overlay must not spawn a subprocess")

    monkeypatch.setattr(subprocess, "run", explode)
    monkeypatch.setattr(subprocess, "check_call", explode)
    apply(project)


def test_dev_dependencies_land_in_the_dev_group(project: Path):
    apply(project)
    pyproject = (project / "pyproject.toml").read_text(encoding="utf-8")

    for requirement in dev_requirements():
        assert f'"{requirement}"' in pyproject
    # Upstream entries survive, and nothing is duplicated.
    assert pyproject.count('"ruff==0.16.2"') == 1
    assert '"django-debug-toolbar==7.0.0"' in pyproject


def test_seed_command_targets_the_installed_app(project: Path):
    apply(project)
    command = (project / "acme/users/management/commands/seed_database.py").read_text()
    assert "from acme.users.tests.factories import UserFactory" in command


def test_legacy_seed_command_outside_installed_apps_is_removed(project: Path):
    legacy = project / "acme/management/commands/seed_database.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('"""Seed the database with development data."""\n', encoding="utf-8")

    apply(project)

    assert not legacy.exists()


def test_system_checks_are_registered_in_base_so_they_run_under_test_settings(project: Path):
    """django-linear-migrations only guards CI if it is installed in base, not local."""
    apply(project)
    base = (project / "config/settings/base.py").read_text(encoding="utf-8")
    local = (project / "config/settings/local.py").read_text(encoding="utf-8")

    assert "django_linear_migrations" in base
    assert "django_version_checks" in base
    assert "VERSION_CHECKS" in base
    # Local-only tooling stays local.
    assert "django_browser_reload" in local
    assert "django_browser_reload" not in base


def test_version_checks_follow_the_project_python_version(project: Path):
    apply(project)
    base = (project / "config/settings/base.py").read_text(encoding="utf-8")
    assert '"python": "~=3.14.0"' in base


def test_logging_extends_upstream_instead_of_replacing_it(project: Path):
    apply(project)
    local = (project / "config/settings/local.py").read_text(encoding="utf-8")

    assert 'LOGGING["handlers"]["console"]' in local
    # A bare `LOGGING = {` in local.py would discard the upstream configuration.
    assert "\nLOGGING = {" not in local


def test_max_migration_files_track_the_latest_migration(project: Path):
    apply(project)
    marker = project / "acme/users/migrations/max_migration.txt"
    assert marker.read_text(encoding="utf-8") == "0002_alter_user\n"


def test_pending_migrations_test_declares_database_access(project: Path):
    """`makemigrations --check` calls check_consistent_history, which opens a connection."""
    apply(project)
    content = (project / "acme/tests/test_pending_migrations.py").read_text(encoding="utf-8")
    assert "@pytest.mark.django_db" in content


def test_urls_patch_degrades_gracefully_without_the_dev_extra(project: Path):
    apply(project)
    urls = (project / "config/urls.py").read_text(encoding="utf-8")
    assert "except ImportError" in urls
    assert "except Exception" not in urls


# ---------------------------------------------------------------------------
# Upgrade semantics
# ---------------------------------------------------------------------------


def test_harness_upgrade_propagates_to_untouched_managed_files(project: Path):
    apply(project)
    state = read_state(project)
    agents = project / "AGENTS.md"

    # Simulate a harness release that ships new AGENTS.md content by rewinding the
    # recorded hash: the file on disk still matches what the overlay last wrote.
    agents.write_text("stale harness content\n", encoding="utf-8")
    state["managed_files"]["AGENTS.md"] = (
        __import__("hashlib")
        .sha256(
            b"stale harness content\n",
        )
        .hexdigest()
    )
    (project / STATE_FILENAME).write_text(json.dumps(state), encoding="utf-8")

    result = apply(project)

    assert "django-ai-harness" in agents.read_text(encoding="utf-8")
    assert ("AGENTS.md", UPDATED) in result.entries


def test_locally_modified_files_are_reported_not_clobbered(project: Path):
    apply(project)
    agents = project / "AGENTS.md"
    agents.write_text("# my own contract\n", encoding="utf-8")

    result = apply(project)

    assert agents.read_text(encoding="utf-8") == "# my own contract\n"
    assert ("AGENTS.md", SKIPPED_LOCAL) in result.entries
    assert result.skipped


def test_force_overwrites_local_modifications(project: Path):
    apply(project)
    agents = project / "AGENTS.md"
    agents.write_text("# my own contract\n", encoding="utf-8")

    apply(project, force=True)

    assert "django-ai-harness" in agents.read_text(encoding="utf-8")


def test_pre_existing_files_are_never_adopted(project: Path):
    agents = project / "AGENTS.md"
    agents.write_text("# written by someone else\n", encoding="utf-8")

    apply(project)

    assert agents.read_text(encoding="utf-8") == "# written by someone else\n"


def test_upgrading_from_a_pre_2_0_state_reports_untracked_files(project: Path):
    """1.x wrote no `managed_files`, so ownership of its files cannot be proven."""
    apply(project)
    (project / STATE_FILENAME).write_text(
        json.dumps({"overlay_version": "1.2.0", "harness": "django-ai-harness"}),
        encoding="utf-8",
    )
    (project / "AGENTS.md").write_text("# written by overlay 1.2.0\n", encoding="utf-8")

    result = apply(project)

    assert ("AGENTS.md", SKIPPED_LEGACY) in result.entries
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "# written by overlay 1.2.0\n"


def test_force_adopts_untracked_files_on_upgrade(project: Path):
    apply(project)
    (project / STATE_FILENAME).write_text(
        json.dumps({"overlay_version": "1.2.0", "harness": "django-ai-harness"}),
        encoding="utf-8",
    )
    (project / "AGENTS.md").write_text("# written by overlay 1.2.0\n", encoding="utf-8")

    apply(project, force=True)

    assert "HackSoft" in (project / "AGENTS.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in read_state(project)["managed_files"]


def test_legacy_marker_blocks_are_rewritten_in_place(project: Path):
    """The v1 marker was a prefix of the pgbouncer one; upgrading must not corrupt it."""
    local = project / "config/settings/local.py"
    local.write_text(
        local.read_text(encoding="utf-8")
        + "\n# >>> django-ai-harness\nOLD_SETTING = True\n# <<< django-ai-harness\n"
        + "\n# >>> django-ai-harness:pgbouncer\nPOOLED = True\n# <<< django-ai-harness:pgbouncer\n",
        encoding="utf-8",
    )

    apply(project)

    text = local.read_text(encoding="utf-8")
    assert "OLD_SETTING" not in text
    assert text.count("# >>> django-ai-harness:local") == 1
    assert text.count("# >>> django-ai-harness:pgbouncer") == 1
    assert "# >>> django-ai-harness\n" not in text


def test_check_mode_reports_without_writing(project: Path):
    result = apply(project, dry_run=True)

    assert result.changed
    assert not (project / "AGENTS.md").exists()
    assert not (project / STATE_FILENAME).exists()


def test_check_mode_is_clean_after_a_real_apply(project: Path):
    apply(project)
    assert not apply(project, dry_run=True).changed


def test_state_file_is_byte_stable_across_runs(project: Path):
    """A timestamp here would make the golden example diff every single run."""
    apply(project)
    first = (project / STATE_FILENAME).read_text(encoding="utf-8")
    apply(project)
    assert (project / STATE_FILENAME).read_text(encoding="utf-8") == first


def test_corrupt_state_file_does_not_break_apply(project: Path):
    apply(project)
    (project / STATE_FILENAME).write_text("{not json", encoding="utf-8")

    apply(project)

    assert read_state(project)["overlay_version"] == OVERLAY_VERSION


# ---------------------------------------------------------------------------
# PgBouncer
# ---------------------------------------------------------------------------


def test_pgbouncer_settings_are_inert_by_default(project: Path):
    apply(project)
    local = (project / "config/settings/local.py").read_text(encoding="utf-8")
    assert 'env.bool("USE_PGBOUNCER", default=False)' in local
    assert read_state(project)["features"]["pgbouncer"] is False


def test_pgbouncer_opt_in_routes_envs_and_defines_a_direct_alias(project: Path):
    apply(project, with_pgbouncer=True)

    postgres_env = (project / ".envs/.local/.postgres").read_text(encoding="utf-8")
    django_env = (project / ".envs/.local/.django").read_text(encoding="utf-8")
    local = (project / "config/settings/local.py").read_text(encoding="utf-8")

    assert "POSTGRES_HOST=pgbouncer" in postgres_env
    assert "POSTGRES_PORT=6432" in postgres_env
    assert "POSTGRES_HOST_DIRECT=postgres" in postgres_env
    assert "USE_PGBOUNCER=True" in django_env
    # The direct alias is what makes POSTGRES_HOST_DIRECT a live setting rather than a
    # comment, and TEST MIRROR keeps the test runner from creating a second database.
    assert 'DATABASES["direct"]' in local
    assert 'env("POSTGRES_HOST_DIRECT"' in local
    assert '"TEST": {"MIRROR": "default"}' in local
    assert read_state(project)["features"]["pgbouncer"] is True


def test_reapplying_without_the_flag_keeps_pgbouncer_enabled(project: Path):
    apply(project, with_pgbouncer=True)
    apply(project)
    assert read_state(project)["features"]["pgbouncer"] is True


def test_pgbouncer_env_routing_is_idempotent(project: Path):
    apply(project, with_pgbouncer=True)
    first = (project / ".envs/.local/.postgres").read_text(encoding="utf-8")
    apply(project, with_pgbouncer=True)
    assert (project / ".envs/.local/.postgres").read_text(encoding="utf-8") == first


def test_pgbouncer_entrypoint_survives_unset_credentials():
    """`set -u` used to abort before the friendly error message could print."""
    from django_ai_harness.pins import data_path  # noqa: PLC0415

    script = (data_path("pgbouncer") / "entrypoint.sh").read_text(encoding="utf-8")
    assert "${POSTGRES_USER:-}" in script
    assert "${POSTGRES_USER}" not in script.replace("${POSTGRES_USER:-}", "")
