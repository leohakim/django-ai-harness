"""Repository-level invariants.

These guard the promises the README makes, so documentation drift becomes a test
failure instead of something a user discovers.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from django_ai_harness import OVERLAY_VERSION
from django_ai_harness import __version__
from django_ai_harness.i18n import LANGUAGES
from django_ai_harness.i18n import MESSAGES
from django_ai_harness.i18n import resolve_language
from django_ai_harness.wizard.steps import DECISIONS
from django_ai_harness.wizard.steps import visible_decisions

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


def test_version_matches_pyproject(pyproject: dict):
    assert pyproject["project"]["version"] == __version__


def test_changelog_documents_the_current_version():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{__version__}]" in changelog


def test_overlay_version_tracks_the_distribution():
    assert __version__ == OVERLAY_VERSION


# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------


def test_every_message_has_every_language():
    for key, entry in MESSAGES.items():
        missing = set(LANGUAGES) - set(entry)
        assert not missing, f"{key} is missing translations: {sorted(missing)}"


def test_every_wizard_string_has_every_language():
    for decision in DECISIONS:
        for field_name in ("title", "subtitle", "why"):
            entry = getattr(decision, field_name)
            assert set(entry) >= set(LANGUAGES), f"{decision.key}.{field_name}"
        for choice in decision.choices:
            for field_name in ("label", "adds", "removes", "implication"):
                entry = getattr(choice, field_name)
                assert set(entry) >= set(LANGUAGES), f"{decision.key}.{choice.value}.{field_name}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("es_AR.UTF-8", "es"), ("en_US.UTF-8", "en"), ("fr_FR", "en"), ("", "en"), ("ES", "es")],
)
def test_resolve_language(value: str, expected: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DJANGO_AI_HARNESS_LANG", raising=False)
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LANG", value)
    assert resolve_language() == expected


# ---------------------------------------------------------------------------
# Wizard catalog
# ---------------------------------------------------------------------------


def test_every_decision_default_is_a_real_choice():
    for decision in DECISIONS:
        values = {choice.value for choice in decision.choices}
        assert decision.default in values, decision.key


def test_decision_keys_are_unique():
    keys = [decision.key for decision in DECISIONS]
    assert len(keys) == len(set(keys))


def test_pgbouncer_is_hidden_without_docker():
    without_docker = {decision.key for decision in visible_decisions({"use_docker": "n"})}
    with_docker = {decision.key for decision in visible_decisions({"use_docker": "y"})}
    assert "with_pgbouncer" not in without_docker
    assert "with_pgbouncer" in with_docker


# ---------------------------------------------------------------------------
# Documentation consistency
# ---------------------------------------------------------------------------


def _markdown_files() -> list[Path]:
    skip = {"example", ".git", ".venv", "node_modules"}
    return [
        path
        for path in REPO_ROOT.rglob("*.md")
        if not skip & set(path.relative_to(REPO_ROOT).parts)
    ]


def test_no_document_claims_env_files_are_committed():
    """`keep_local_envs_in_vcs=n` means `.envs/` never lands in the repository."""
    security = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "example/.envs/` contains" not in security
    assert "**not** committed" in security


_RELATIVE_LINK_RE = re.compile(r"\[[^\]]*\]\((?!https?://|mailto:|#)([^)#\s]+)")


def test_every_relative_link_resolves():
    """Documentation links are load-bearing: a dead one sends a reader nowhere."""
    broken = []
    for path in _markdown_files():
        broken.extend(
            f"{path.relative_to(REPO_ROOT)} -> {target}"
            for target in _RELATIVE_LINK_RE.findall(path.read_text(encoding="utf-8"))
            if not (path.parent / target).exists()
        )
    assert not broken, broken


def test_docs_do_not_instruct_removed_entry_points():
    """Prose may explain why something was removed; instructions may not still use it."""
    removed_commands = (
        "./scripts/new-project.sh <target",
        "python scripts/lib/",
        "uv run scripts/wizard",
        "--harness-root .",
        "WITH_PGBOUNCER=1",
    )
    offenders = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        offenders += [
            f"{path.relative_to(REPO_ROOT)}: {needle}"
            for needle in removed_commands
            if needle in text
        ]
    assert not offenders, offenders


def test_golden_example_carries_no_generated_secret():
    """Regeneration normalises the random SECRET_KEY so the tree stays comparable.

    A real generated key here would both churn the diff on every run and look like a
    committed credential to anyone reading the repository.
    """
    placeholder = "django-ai-harness-golden-example-secret-key-not-for-real-use-0001"
    for relative in ("config/settings/local.py", "config/settings/test.py"):
        path = REPO_ROOT / "example" / relative
        if not path.exists():  # pragma: no cover - example not generated yet
            continue
        assert placeholder in path.read_text(encoding="utf-8"), relative


def test_readme_documents_the_published_entry_point():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "uvx django-ai-harness new" in readme
    assert "uvx django-ai-harness apply" in readme


def test_release_environment_matches_the_documented_trusted_publisher():
    """PyPI matches the OIDC claim on workflow *and* environment name.

    Renaming either without updating the publisher on PyPI makes releases fail at the
    publish step, after a green build — so the documented values are load-bearing.
    """
    release = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    maintaining = (REPO_ROOT / "docs/maintaining.md").read_text(encoding="utf-8")

    assert "name: pypi" in release
    assert "`pypi`" in maintaining
    assert "`release.yml`" in maintaining


def test_pending_setup_is_recorded():
    """One-time setup that is not done yet stays visible instead of living in a memory."""
    maintaining = (REPO_ROOT / "docs/maintaining.md").read_text(encoding="utf-8")
    assert "## Pending setup" in maintaining
    for item in ("Trusted Publishing", "Discussions"):
        assert item in maintaining, item


def test_docker_requirement_is_documented_where_users_hit_it():
    """cookiecutter-django resolves dependencies in a container when use_docker=y."""
    for relative in ("README.md", "docs/getting-started.md", "CONTRIBUTING.md"):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "Docker" in text, relative
    getting_started = (REPO_ROOT / "docs/getting-started.md").read_text(encoding="utf-8")
    assert "137" in getting_started


def test_claude_settings_are_valid_and_portable():
    """A malformed settings.json silently disables every rule in it.

    The file is committed, so it must also stay portable: an absolute path scopes a rule
    to one machine, which both leaks the author's home directory into a public repository
    and makes the rule a no-op for every other contributor.
    """
    import json  # noqa: PLC0415

    settings = json.loads((REPO_ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    permissions = settings["permissions"]

    assert permissions["allow"], "the allow list should not be empty"
    for rule in permissions["allow"] + permissions["deny"]:
        assert "/Users/" not in rule, rule
        assert not rule.startswith("/"), rule

    # Publishing is irreversible and belongs to CI, not to a local shell.
    denied = " ".join(permissions["deny"])
    assert "uv publish" in denied
    assert "twine upload" in denied
    assert "git push --tags" in denied


def test_personal_claude_settings_are_gitignored():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".claude/settings.local.json" in gitignore


def test_shell_scripts_are_executable_and_strict():
    for script in sorted((REPO_ROOT / "scripts").glob("*.sh")):
        text = script.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash"), script.name
        assert "set -euo pipefail" in text, script.name
        assert script.stat().st_mode & 0o111, f"{script.name} is not executable"


def test_skills_declare_frontmatter():
    for skill in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n"), skill
        frontmatter = text.split("---", 2)[1]
        assert re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE), skill
        assert re.search(r"^description:\s*\S+", frontmatter, re.MULTILINE), skill
