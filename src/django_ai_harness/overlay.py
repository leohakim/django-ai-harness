"""Apply the django-ai-harness overlay onto a cookiecutter-django project.

Design contract
---------------

The overlay is **idempotent**, **hermetic** and **upgrade-aware**:

*Idempotent*
    Running it twice produces the same tree. Settings patches live inside uniquely
    named marker blocks that are replaced in place, never appended twice.

*Hermetic*
    It never touches the network and never shells out to a resolver. DX dependencies
    come from ``data/dev-requirements.txt`` with ``==`` pins and are written straight
    into ``[dependency-groups].dev``. This is what makes regeneration of the golden
    ``example/`` reproducible: a new release on PyPI can no longer change the output.

*Upgrade-aware*
    Every file the overlay owns is recorded in ``.django-ai-harness.json`` together
    with the SHA-256 of the content the overlay last wrote. On re-apply:

    ==========================  ==========================================
    File state                  Action
    ==========================  ==========================================
    missing                     write it
    matches the new content     nothing to do
    matches what we last wrote  update it (harness upgrade propagates)
    locally modified            skip and report (``--force`` overrides)
    existed before the overlay  skip and report (``--force`` adopts it)
    ==========================  ==========================================
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from django_ai_harness import OVERLAY_VERSION
from django_ai_harness.pins import Requirement
from django_ai_harness.pins import data_path
from django_ai_harness.pins import dev_requirements
from django_ai_harness.pins import normalize_name

__all__ = ["OVERLAY_VERSION", "OverlayError", "OverlayResult", "apply", "main"]

STATE_FILENAME = ".django-ai-harness.json"

#: ``.python-version`` needs at least major and minor to build a `~=` specifier.
_MIN_VERSION_PARTS = 2

# Marker names are suffixed so that no marker is a prefix of another one. The bare
# `# >>> django-ai-harness` markers written by overlay < 2.0 are migrated on contact.
LEGACY_BEGIN = "# >>> django-ai-harness"
LEGACY_END = "# <<< django-ai-harness"

_PYPROJECT_DEV_GROUP_RE = re.compile(r"^dev\s*=\s*\[\n(?P<body>.*?)^\]", re.MULTILINE | re.DOTALL)
_QUOTED_RE = re.compile(r'"([^"]+)"')
_SKIP_DIRS = frozenset(
    {
        ".git",
        ".github",
        ".idea",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "config",
        "docs",
        "harness_templates",
        "locale",
        "node_modules",
        "requirements",
        "tests",
        "utility",
        "venv",
    },
)


class OverlayError(RuntimeError):
    """Raised when the target tree is not a cookiecutter-django project."""


# --------------------------------------------------------------------------------------
# Result reporting
# --------------------------------------------------------------------------------------

CREATED = "created"
UPDATED = "updated"
UNCHANGED = "unchanged"
SKIPPED_LOCAL = "skipped (local edits)"
SKIPPED_FOREIGN = "skipped (pre-existing file)"
SKIPPED_LEGACY = "skipped (untracked, pre-2.0)"

_DIRTY_STATUSES = frozenset({CREATED, UPDATED})


@dataclass
class OverlayResult:
    """Outcome of one overlay run."""

    project_root: Path
    package: str
    entries: list[tuple[str, str]] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(status in _DIRTY_STATUSES for _, status in self.entries)

    @property
    def skipped(self) -> list[tuple[str, str]]:
        return [(label, status) for label, status in self.entries if status.startswith("skipped")]

    def record(self, label: str, status: str) -> str:
        self.entries.append((label, status))
        return status


@dataclass
class Overlay:
    """Applies the overlay to a single project tree."""

    project_root: Path
    dry_run: bool = False
    force: bool = False
    state: dict = field(default_factory=dict)
    result: OverlayResult = field(init=False)
    package: str = field(init=False)
    #: True when upgrading a project whose state file predates file-ownership tracking.
    legacy_state: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.project_root = self.project_root.resolve()
        self.package = find_project_package(self.project_root)
        self.state = read_state(self.project_root)
        # Overlay < 2.0 wrote a state file without `managed_files`. Those projects do have
        # overlay-owned files, we just cannot prove which ones the user has since edited,
        # so they are reported under their own status rather than silently overwritten.
        self.legacy_state = bool(self.state) and "managed_files" not in self.state
        self.result = OverlayResult(project_root=self.project_root, package=self.package)

    # -- primitives ---------------------------------------------------------------

    @property
    def _managed(self) -> dict:
        return self.state.setdefault("managed_files", {})

    def _write(self, path: Path, content: str) -> None:
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_managed(self, rel: str, content: str) -> str:
        """Write a file the overlay owns, respecting local modifications."""
        path = self.project_root / rel
        digest = _sha256(content)
        recorded = self._managed.get(rel)

        if not path.exists():
            self._write(path, content)
            self._managed[rel] = digest
            return self.result.record(rel, CREATED)

        current = _sha256(path.read_text(encoding="utf-8"))
        if current == digest:
            self._managed[rel] = digest
            return self.result.record(rel, UNCHANGED)

        if recorded is None:
            if self.force:
                self._write(path, content)
                self._managed[rel] = digest
                return self.result.record(rel, UPDATED)
            # The file predates the overlay (or was written by another tool). Never clobber.
            status = SKIPPED_LEGACY if self.legacy_state else SKIPPED_FOREIGN
            return self.result.record(rel, status)

        if current == recorded or self.force:
            self._write(path, content)
            self._managed[rel] = digest
            return self.result.record(rel, UPDATED)

        return self.result.record(rel, SKIPPED_LOCAL)

    def write_if_missing(self, rel: str, content: str) -> str:
        """Create structural files (package ``__init__`` markers) without tracking them."""
        path = self.project_root / rel
        if path.exists():
            return UNCHANGED
        self._write(path, content)
        return CREATED

    def upsert_block(self, rel: str, name: str, body: str, *, label: str | None = None) -> str:
        """Insert or replace a uniquely named marker block inside an existing file."""
        path = self.project_root / rel
        if not path.exists():
            return self.result.record(label or f"{rel} [{name}]", SKIPPED_FOREIGN)

        original = path.read_text(encoding="utf-8")
        text = migrate_legacy_markers(original, name)
        updated = upsert_marked_block(text, name, body)
        entry = label or f"{rel} [{name}]"
        if updated == original:
            return self.result.record(entry, UNCHANGED)
        self._write(path, updated)
        return self.result.record(entry, CREATED if text == original else UPDATED)

    # -- steps --------------------------------------------------------------------

    def sync_dev_dependencies(self) -> str:
        pyproject = self.project_root / "pyproject.toml"
        if not pyproject.exists():
            msg = f"pyproject.toml missing in {self.project_root} — is this cookiecutter-django?"
            raise OverlayError(msg)
        original = pyproject.read_text(encoding="utf-8")
        updated = merge_dev_requirements(original, dev_requirements())
        if updated == original:
            return self.result.record("pyproject.toml [dev deps]", UNCHANGED)
        self._write(pyproject, updated)
        return self.result.record("pyproject.toml [dev deps]", UPDATED)

    def patch_base_settings(self) -> str:
        version_checks = _python_requirement(self.project_root)
        body = f"""# Settings hygiene (see knowledge/dx-practices/settings.md):
# - Import `django.conf.settings` from app code, never this module directly.
# - Never mutate settings at runtime from request or business code.
# - Keep secrets and environment-specific values in env vars, local.py or production.py.

# django-linear-migrations and django-version-checks register *system checks*, so they
# belong in base settings: that is the only way they also run under config.settings.test
# (which imports base, not local) and therefore in CI.
INSTALLED_APPS += ["django_linear_migrations", "django_version_checks"]

VERSION_CHECKS = {{
    "python": "{version_checks}",
}}
"""
        return self.upsert_block("config/settings/base.py", "base", body)

    def patch_local_settings(self) -> str:
        body = """# Local-only developer experience. Anything here is intentionally absent from
# production and from config.settings.test.
INSTALLED_APPS += ["django_browser_reload", "django_read_only", "django_rich"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# django-read-only guards against accidental writes in an interactive shell.
# It stays inert until you opt in:
#     import django_read_only; django_read_only.enable()
# Prefer IPython for `shell_plus`.
SHELL_PLUS = "ipython"

# Rich console logging. We deliberately patch the handler that base.py already defines
# instead of replacing LOGGING wholesale, so upstream loggers and formatters survive.
LOGGING["formatters"]["rich"] = {"datefmt": "[%X]"}
LOGGING["handlers"]["console"] = {
    "level": "DEBUG",
    "class": "rich.logging.RichHandler",
    "formatter": "rich",
    "rich_tracebacks": True,
}
"""
        return self.upsert_block("config/settings/local.py", "local", body)

    def patch_urls(self) -> str:
        body = """if settings.DEBUG:
    try:
        import django_browser_reload  # noqa: F401
    except ImportError:  # pragma: no cover - dev extra not installed
        pass
    else:
        urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
"""
        return self.upsert_block("config/urls.py", "urls", body)

    def patch_pgbouncer_settings(self) -> str:
        body = """# Opt-in transaction pooling. Inert unless USE_PGBOUNCER is set; the engine stays
# PostgreSQL either way. See knowledge/dx-practices/postgres-pooling.md.
if env.bool("USE_PGBOUNCER", default=False):
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
    # PgBouncer in transaction mode cannot hold server-side cursors across statements.
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

    # A direct, unpooled alias for DDL. Run migrations with:
    #     python manage.py migrate --database=direct
    # TEST["MIRROR"] keeps the test runner from creating a second test database.
    DATABASES["direct"] = {
        **DATABASES["default"],
        "HOST": env("POSTGRES_HOST_DIRECT", default="postgres"),
        "PORT": env.int("POSTGRES_PORT_DIRECT", default=5432),
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": False,
        "TEST": {"MIRROR": "default"},
    }
"""
        statuses = [
            self.upsert_block(f"config/settings/{name}", "pgbouncer", body)
            for name in ("local.py", "production.py")
        ]
        return UPDATED if any(s in _DIRTY_STATUSES for s in statuses) else UNCHANGED

    def add_agents_md(self) -> str:
        return self.write_managed("AGENTS.md", _AGENTS_MD)

    def add_project_doc(self) -> str:
        return self.write_managed("docs/django-ai-harness.md", _PROJECT_DOC)

    def add_seed_command(self) -> str:
        base = f"{self.package}/users/management"
        self.write_if_missing(f"{base}/__init__.py", "")
        self.write_if_missing(f"{base}/commands/__init__.py", "")
        status = self.write_managed(
            f"{base}/commands/seed_database.py",
            _SEED_COMMAND.format(package=self.package),
        )
        self._drop_legacy_seed_command()
        return status

    def _drop_legacy_seed_command(self) -> None:
        """Overlay < 1.1 installed the command outside INSTALLED_APPS, where it never loaded."""
        legacy = self.project_root / self.package / "management" / "commands" / "seed_database.py"
        if not legacy.exists():
            return
        try:
            text = legacy.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover - unreadable file
            return
        if "Seed the database with development data" not in text:
            return
        if not self.dry_run:
            legacy.unlink()
            for parent in (legacy.parent, legacy.parent.parent):
                _remove_if_trivial_package(parent)
        self.result.record(str(legacy.relative_to(self.project_root)), "removed (legacy path)")

    def add_pending_migrations_test(self) -> str:
        self.write_if_missing(f"{self.package}/tests/__init__.py", "")
        return self.write_managed(
            f"{self.package}/tests/test_pending_migrations.py",
            _PENDING_MIGRATIONS_TEST,
        )

    def add_app_skeleton(self) -> str:
        statuses = [
            self.write_managed(f"harness_templates/app_skeleton/{rel}", content)
            for rel, content in _APP_SKELETON.items()
        ]
        return _worst(statuses)

    def add_pgbouncer_templates(self) -> str:
        source = data_path("pgbouncer")
        if not source.is_dir():  # pragma: no cover - packaging error
            msg = f"missing packaged pgbouncer templates at {source}"
            raise OverlayError(msg)
        mapping = {
            "README.md": "compose/pgbouncer/README.md",
            "entrypoint.sh": "compose/pgbouncer/entrypoint.sh",
            "postgres/tuning-small.conf": "compose/pgbouncer/postgres/tuning-small.conf",
            "postgres/tuning-medium.conf": "compose/pgbouncer/postgres/tuning-medium.conf",
            "docker-compose.pgbouncer.yml": "docker-compose.pgbouncer.yml",
        }
        statuses = []
        for rel, dest in mapping.items():
            statuses.append(self.write_managed(dest, (source / rel).read_text(encoding="utf-8")))
            target = self.project_root / dest
            if dest.endswith(".sh") and target.exists() and not self.dry_run:
                target.chmod(target.stat().st_mode | 0o111)
        return _worst(statuses)

    def enable_pgbouncer_envs(self) -> str:
        django_body = """USE_PGBOUNCER=True
CONN_MAX_AGE=0
"""
        postgres_body = """# Direct Postgres, bypassing the pooler, for migrations and other DDL:
#     python manage.py migrate --database=direct
POSTGRES_HOST_DIRECT=postgres
POSTGRES_PORT_DIRECT=5432
"""
        statuses = []
        for env_name in (".local", ".production"):
            statuses.append(
                self._route_postgres_env(f".envs/{env_name}/.postgres", postgres_body),
            )
            statuses.append(
                self.upsert_block(f".envs/{env_name}/.django", "pgbouncer", django_body)
            )
        return _worst(statuses)

    def _route_postgres_env(self, rel: str, body: str) -> str:
        path = self.project_root / rel
        if not path.exists():
            return self.result.record(f"{rel} [pgbouncer]", SKIPPED_FOREIGN)
        original = path.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^POSTGRES_HOST=.*$", "POSTGRES_HOST=pgbouncer", original)
        text = re.sub(r"(?m)^POSTGRES_PORT=.*$", "POSTGRES_PORT=6432", text)
        text = upsert_marked_block(text, "pgbouncer", body)
        if text == original:
            return self.result.record(f"{rel} [pgbouncer]", UNCHANGED)
        self._write(path, text)
        return self.result.record(f"{rel} [pgbouncer]", UPDATED)

    def ensure_linear_migration_files(self) -> str:
        """Create the ``max_migration.txt`` files django-linear-migrations checks."""
        statuses = []
        for migrations_dir in sorted(self.project_root.rglob("migrations")):
            if not migrations_dir.is_dir() or migrations_dir.name != "migrations":
                continue
            if _SKIP_DIRS & set(migrations_dir.parts) or "site-packages" in migrations_dir.parts:
                continue
            if not (migrations_dir / "__init__.py").exists():
                continue
            modules = sorted(
                path.stem for path in migrations_dir.glob("*.py") if not path.name.startswith("_")
            )
            if not modules:
                continue
            rel = (migrations_dir / "max_migration.txt").relative_to(self.project_root)
            statuses.append(self.write_managed(str(rel), modules[-1] + "\n"))
        return _worst(statuses) if statuses else UNCHANGED

    def write_state(self, *, with_pgbouncer: bool) -> None:
        # Re-applying without the flag must never silently disable an enabled opt-in.
        previously_enabled = bool(self.state.get("features", {}).get("pgbouncer", False))
        payload = {
            "harness": "django-ai-harness",
            "overlay_version": OVERLAY_VERSION,
            "features": {"pgbouncer": with_pgbouncer or previously_enabled},
            # SHA-256 of the content the overlay last wrote, so a later run can tell a
            # harness upgrade apart from a local edit. Deliberately no timestamps: the
            # state file has to stay byte-stable for the golden example diff.
            "managed_files": dict(sorted(self._managed.items())),
        }
        if not self.dry_run:
            (self.project_root / STATE_FILENAME).write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )


# --------------------------------------------------------------------------------------
# Pure helpers (unit-tested directly)
# --------------------------------------------------------------------------------------


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _worst(statuses: list[str]) -> str:
    for candidate in (SKIPPED_LOCAL, SKIPPED_FOREIGN, UPDATED, CREATED):
        if candidate in statuses:
            return candidate
    return UNCHANGED


def _remove_if_trivial_package(directory: Path) -> None:
    """Delete a leftover package directory that only holds an empty ``__init__.py``."""
    if not directory.is_dir():
        return
    children = list(directory.iterdir())
    if children and children != [directory / "__init__.py"]:
        return
    if children and (directory / "__init__.py").read_text(encoding="utf-8").strip():
        return
    for child in children:
        child.unlink()
    directory.rmdir()


def block_markers(name: str) -> tuple[str, str]:
    """Return the begin/end markers for a named overlay block."""
    return f"{LEGACY_BEGIN}:{name}", f"{LEGACY_END}:{name}"


def _block_pattern(begin: str, end: str) -> re.Pattern[str]:
    # Anchored to whole lines so that `:pgbouncer` can never be matched by the shorter
    # `:local` marker, which is exactly how overlay 1.x could corrupt a settings file.
    return re.compile(
        rf"^{re.escape(begin)}$\n.*?^{re.escape(end)}$\n?",
        re.DOTALL | re.MULTILINE,
    )


def upsert_marked_block(text: str, name: str, body: str) -> str:
    """Insert ``body`` as a named marker block, replacing any previous instance."""
    begin, end = block_markers(name)
    block = f"{begin}\n{body.rstrip()}\n{end}\n"
    pattern = _block_pattern(begin, end)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    if text and not text.endswith("\n"):
        text += "\n"
    separator = "\n" if text else ""
    return text + separator + block


def migrate_legacy_markers(text: str, name: str) -> str:
    """Rename overlay < 2.0 bare markers to their namespaced equivalent.

    The bare markers are a prefix of every namespaced marker, so they are matched with a
    line anchor to avoid rewriting ``# >>> django-ai-harness:pgbouncer``.
    """
    begin, end = block_markers(name)
    text = re.sub(rf"(?m)^{re.escape(LEGACY_BEGIN)}$", begin, text)
    return re.sub(rf"(?m)^{re.escape(LEGACY_END)}$", end, text)


def merge_dev_requirements(pyproject_text: str, requirements: list[Requirement]) -> str:
    """Merge pinned requirements into ``[dependency-groups].dev``, sorted by project name.

    Existing entries for the same project are replaced, so re-running never duplicates a
    dependency and a version bump in ``dev-requirements.txt`` propagates cleanly.
    """
    match = _PYPROJECT_DEV_GROUP_RE.search(pyproject_text)
    if match is None:
        rendered = _render_requirements(sorted(requirements, key=normalize_name))
        prefix = "" if pyproject_text.endswith("\n") else "\n"
        return f"{pyproject_text}{prefix}\n[dependency-groups]\ndev = [\n{rendered}]\n"

    existing = _QUOTED_RE.findall(match.group("body"))
    merged = {normalize_name(item): item for item in existing}
    merged.update({normalize_name(item): str(item) for item in requirements})
    rendered = _render_requirements([merged[key] for key in sorted(merged)])
    return pyproject_text[: match.start("body")] + rendered + pyproject_text[match.end("body") :]


def _render_requirements(items: list[str]) -> str:
    return "".join(f'  "{item}",\n' for item in items)


def find_project_package(project_root: Path) -> str:
    """Detect the nested Django package of a cookiecutter-django two-tier layout."""
    if not (project_root / "manage.py").exists():
        msg = f"manage.py not found in {project_root} — is this a Django project?"
        raise OverlayError(msg)
    for child in sorted(project_root.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name in _SKIP_DIRS:
            continue
        if (child / "users").is_dir() or (child / "conftest.py").exists():
            return child.name
    msg = (
        f"could not detect the project package inside {project_root}: expected a directory "
        "containing users/ or conftest.py (cookiecutter-django layout)"
    )
    raise OverlayError(msg)


def read_state(project_root: Path) -> dict:
    """Read ``.django-ai-harness.json``, tolerating corruption from manual edits."""
    path = project_root / STATE_FILENAME
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return state if isinstance(state, dict) else {}


def _python_requirement(project_root: Path) -> str:
    """Build the django-version-checks spec from the project's own ``.python-version``."""
    version_file = project_root / ".python-version"
    if version_file.exists():
        parts = version_file.read_text(encoding="utf-8").strip().split(".")
        if len(parts) >= _MIN_VERSION_PARTS and parts[0].isdigit() and parts[1].isdigit():
            return f"~={parts[0]}.{parts[1]}.0"
    return f"~={sys.version_info.major}.{sys.version_info.minor}.0"


# --------------------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------------------


def apply(
    project_root: Path,
    *,
    with_pgbouncer: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> OverlayResult:
    """Apply the overlay to ``project_root`` and return what changed."""
    overlay = Overlay(project_root=Path(project_root), dry_run=dry_run, force=force)

    overlay.sync_dev_dependencies()
    overlay.add_agents_md()
    overlay.patch_base_settings()
    overlay.patch_local_settings()
    overlay.patch_urls()
    overlay.add_seed_command()
    overlay.add_pending_migrations_test()
    overlay.add_project_doc()
    overlay.add_app_skeleton()
    overlay.ensure_linear_migration_files()
    overlay.add_pgbouncer_templates()
    overlay.patch_pgbouncer_settings()
    if with_pgbouncer:
        overlay.enable_pgbouncer_envs()
    overlay.write_state(with_pgbouncer=with_pgbouncer)
    return overlay.result


def _report(result: OverlayResult, *, dry_run: bool) -> None:
    for label, status in result.entries:
        if status == UNCHANGED:
            continue
        print(f"  {status:<26} {label}")
    if not result.changed:
        print("  everything already up to date")
    if result.skipped:
        legacy = any(status == SKIPPED_LEGACY for _, status in result.skipped)
        if legacy:
            print(
                "\nThis project was created by an overlay older than 2.0, which did not "
                "record\nwhich files it owned. The files below were left untouched:",
            )
        else:
            print(
                "\nSome files were kept because they differ from what the overlay last "
                "wrote.\nReview them, then re-run with --force to overwrite:",
            )
        for label, _ in result.skipped:
            print(f"  - {label}")
        if legacy:
            print(
                "\nCommit your work first, then re-run with --force to adopt the current "
                "harness\nversions, and review the diff. From then on your edits are "
                "tracked and preserved.",
            )
    if dry_run and result.changed:
        print("\n--check: the overlay is out of date for this project")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="django-ai-harness apply",
        description="Apply the django-ai-harness overlay to a cookiecutter-django project.",
    )
    parser.add_argument("project_root", type=Path, help="Path to the generated Django project")
    parser.add_argument(
        "--with-pgbouncer",
        action="store_true",
        help=(
            "Route .envs through the pooler (POSTGRES_HOST=pgbouncer, USE_PGBOUNCER=True). "
            "Compose templates and env-gated settings are installed either way."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite every file the overlay owns, including ones it did not write. "
            "Commit your work first."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report what would change and exit 1 if anything is out of date. Writes nothing.",
    )
    args = parser.parse_args(argv)

    try:
        result = apply(
            args.project_root,
            with_pgbouncer=args.with_pgbouncer,
            dry_run=args.check,
            force=args.force,
        )
    except OverlayError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"django-ai-harness overlay v{OVERLAY_VERSION} -> {result.project_root}")
    print(f"Project package: {result.package}")
    _report(result, dry_run=args.check)

    if args.check:
        return 1 if result.changed else 0
    if result.changed:
        print("\nNext: uv sync && uv run python manage.py check")
    return 0


# --------------------------------------------------------------------------------------
# File payloads
# --------------------------------------------------------------------------------------

_AGENTS_MD = """# AGENTS.md

Bootstrapped with [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django)
and [django-ai-harness](https://github.com/leohakim/django-ai-harness).

This file is the contract every agent working in this repository follows. It is owned by
the harness overlay: edit it freely, but be aware that a locally edited copy stops
receiving harness upgrades until you re-run the overlay with `--force`.

## Architecture — HackSoft Django Styleguide

| Concern | Home |
|---|---|
| Writes, workflows, side effects | `services.py` / `services/` |
| Reads, filtering, visibility | `selectors.py` / `selectors/` |
| HTTP input & output | thin APIs calling services and selectors |
| Simple non-relational invariants | `Model.clean` or database constraints |

Business rules never live in views, serializers, forms, signals, `Model.save`, custom
managers or querysets. See `harness_templates/app_skeleton/` for the reference layout.

- Services take keyword-only arguments, call `full_clean()` before saving, and wrap
  multi-step writes in `transaction.atomic`.
- Selectors never mutate state.
- Side effects that depend on committed rows run in `transaction.on_commit`.
- Tests mirror the layers: `tests/services/`, `tests/selectors/`, `tests/apis/`.

## Developer experience

- Run everything through `uv run`; the lockfile is the source of truth.
- Keep Ruff and pre-commit green before proposing a change.
- Seed local data with `python manage.py seed_database` plus Factory Boy factories.
- Migrations are linear: `django-linear-migrations` maintains `max_migration.txt`.
  Resolve conflicts with `python manage.py rebase_migration <app>`.
- `django-read-only` is available for safe shell sessions:
  `import django_read_only; django_read_only.enable()`.

## Harness

- State lives in `.django-ai-harness.json`. Do not hand-edit it.
- Upgrade with `django-ai-harness apply .` (add `--check` in CI to detect drift).
- Optional PostgreSQL connection pooling lives in `compose/pgbouncer/`.

## Skills

If the harness Agent Skills are available, use `django-hacksoft` for feature work and
`django-dx-review` before opening a pull request.
"""

_PROJECT_DOC = """# django-ai-harness

This project carries the [django-ai-harness](https://github.com/leohakim/django-ai-harness)
overlay: a set of developer-experience defaults and an architecture contract shared by
humans and AI agents.

## Upgrading the harness

```bash
uvx django-ai-harness apply .          # or: uv run django-ai-harness apply .
uv sync
uv run python manage.py check
```

The overlay is idempotent and tracks the files it owns in `.django-ai-harness.json`.
Files you edited locally are never overwritten; they are reported instead, and
`--force` overrides that protection once you have reviewed the diff.

Add `--check` to fail CI when the project has drifted from the pinned harness version.

## Where things live

| Path | Purpose |
|---|---|
| `AGENTS.md` | Architecture and DX contract for agents and humans |
| `harness_templates/app_skeleton/` | Reference services / selectors / API layout |
| `compose/pgbouncer/` | Opt-in PostgreSQL connection pooling |
| `.django-ai-harness.json` | Overlay version and managed-file state |

## Connection pooling

PgBouncer is opt-in and keeps PostgreSQL as the engine. Enable it with
`django-ai-harness apply . --with-pgbouncer` and read `compose/pgbouncer/README.md`.
"""

_SEED_COMMAND = '''"""Seed the local database with development data.

Extend this command as the domain grows: it is the one entry point that both humans and
agents use to get a realistic local dataset, which keeps fixtures out of the test suite.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed the database with development data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=3,
            help="Number of users to create (default: 3).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            from {package}.users.tests.factories import UserFactory
        except ImportError as exc:  # pragma: no cover - factories are project-specific
            msg = f"Could not import UserFactory: {{exc}}"
            self.stderr.write(self.style.ERROR(msg))
            self.stdout.write("Add factories, then extend this command for your domain.")
            return

        users = UserFactory.create_batch(options["users"])
        self.stdout.write(self.style.SUCCESS(f"Created {{len(users)}} users"))
'''

_PENDING_MIGRATIONS_TEST = '''"""Guard against models that drifted away from their migrations.

A model change without a migration passes every other test and then fails on deploy, so
this belongs in the suite rather than in a pre-deploy checklist.

`makemigrations --check` verifies the migration graph against the model state and also
calls `check_consistent_history`, which opens a database connection — hence the
`django_db` mark.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_no_pending_migrations():
    try:
        call_command("makemigrations", check=True, dry_run=True, verbosity=0)
    except SystemExit as exc:  # Django exits non-zero when changes are missing.
        if exc.code not in (None, 0):
            pytest.fail(
                "Model changes are missing migrations. "
                "Run `python manage.py makemigrations` and commit the result.",
            )
'''

_APP_SKELETON = {
    "README.md": """# App skeleton (HackSoft Django Styleguide)

Copy this layout into every new app. It is a reference, not an installed package.

```text
<app>/
├── models.py       # data + simple non-relational invariants
├── services.py     # writes, workflows, side effects
├── selectors.py    # reads, filtering, visibility
├── apis/           # one operation per class, thin
└── tests/
    ├── services/
    ├── selectors/
    └── apis/
```

Rules of thumb:

- If it writes or orchestrates, it is a service.
- If it reads or filters, it is a selector.
- If a rule can be expressed as a database constraint, prefer the constraint.
- Interfaces (APIs, forms, admin, tasks, management commands) call services and
  selectors; they never own business rules.
""",
    "services.py": '''"""Write-side business logic.

Services own workflows and side effects. They take keyword-only arguments, validate
with `full_clean()` before saving, and wrap multi-step writes in a transaction.
"""

from __future__ import annotations

from django.db import transaction


@transaction.atomic
def example_create(*, name: str) -> None:
    """Replace with a real domain service."""
    raise NotImplementedError
''',
    "selectors.py": '''"""Read-side queries.

Selectors answer questions. They may return querysets, iterables, objects, ids or
shaped data, and they never mutate state.
"""

from __future__ import annotations

from django.db.models import QuerySet


def example_list() -> QuerySet:
    """Replace with a real domain selector."""
    raise NotImplementedError
''',
    "apis/__init__.py": "",
    "apis/example.py": '''"""Thin API: validate input, call a service or selector, serialize output.

One operation per class. Input and output serializers are nested so they stay local to
the operation instead of becoming a shared, over-general schema.
"""

from rest_framework import serializers
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class ExampleCreateApi(APIView):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=255)

    class OutputSerializer(serializers.Serializer):
        id = serializers.IntegerField()
        name = serializers.CharField()

    def post(self, request: Request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # services.example_create(**serializer.validated_data)
        return Response(
            {"detail": "not implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
''',
}


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
