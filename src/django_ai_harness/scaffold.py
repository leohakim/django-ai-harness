"""Generate a cookiecutter-django project and apply the harness overlay.

The cookiecutter *Python API* is used rather than the CLI: the context is passed as a
dictionary, so project names, descriptions and domains cannot break `key=value` parsing
and need no escaping.
"""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from django_ai_harness import overlay as overlay_module
from django_ai_harness.i18n import Translator
from django_ai_harness.pins import cookiecutter_ref

__all__ = ["ProjectConfig", "ScaffoldError", "next_steps", "sanitize_slug", "scaffold"]

COOKIECUTTER_TEMPLATE = "gh:cookiecutter/cookiecutter-django"

_ILLEGAL_CONTEXT_RE = re.compile(r"[\x00-\x1f\x7f]")
_SLUG_STRIP_RE = re.compile(r"[^0-9a-zA-Z_]")


class ScaffoldError(RuntimeError):
    """Raised when the project cannot be generated."""


def sanitize_context_value(value: str, *, field_name: str) -> str:
    """Reject control characters that would corrupt the generated files."""
    if _ILLEGAL_CONTEXT_RE.search(value):
        msg = f"invalid control character in {field_name!r}"
        raise ValueError(msg)
    return value.strip()


def sanitize_slug(raw: str) -> str:
    """Turn a directory name into a valid Python package identifier."""
    slug = raw.strip().replace("-", "_").replace(".", "_").replace(" ", "_")
    slug = _SLUG_STRIP_RE.sub("", slug)
    if not slug:
        msg = "project slug cannot be empty"
        raise ValueError(msg)
    if slug[0].isdigit():
        slug = f"p_{slug}"
    if not slug.isidentifier() or slug in {"test", "django", "config"}:
        msg = f"{slug!r} is not a usable Python package name"
        raise ValueError(msg)
    return slug


@dataclass
class ProjectConfig:
    """Everything cookiecutter-django and the overlay need to generate a project."""

    target: Path
    project_name: str
    description: str = "Project managed with django-ai-harness"
    author_name: str = "django-ai-harness"
    domain_name: str = "example.com"
    email: str = ""
    open_source_license: str = "MIT"
    username_type: str = "email"
    timezone: str = "UTC"
    use_docker: str = "y"
    postgresql_version: str = "16"
    cloud_provider: str = "None"
    mail_service: str = "Other SMTP"
    rest_api: str = "DRF"
    use_async: str = "n"
    frontend_pipeline: str = "None"
    use_celery: str = "n"
    mail_catcher: str = "None"
    use_sentry: str = "n"
    use_whitenoise: str = "y"
    use_heroku: str = "n"
    ci_tool: str = "Github"
    with_pgbouncer: bool = False
    project_slug: str = ""
    cookiecutter_ref: str = ""
    language: str = field(default="en")

    def __post_init__(self) -> None:
        self.target = Path(self.target).expanduser().resolve()
        if self.with_pgbouncer:
            # A pooler only exists in the Compose topology the template generates.
            self.use_docker = "y"
        self.project_slug = sanitize_slug(self.project_slug or self.target.name)
        self.cookiecutter_ref = self.cookiecutter_ref or cookiecutter_ref()
        self.email = self.email or f"hello@{self.domain_name}"
        for name in ("project_name", "description", "author_name", "domain_name", "email"):
            setattr(self, name, sanitize_context_value(getattr(self, name), field_name=name))

    def as_cookiecutter_context(self) -> dict[str, str]:
        return {
            "project_name": self.project_name,
            "project_slug": self.project_slug,
            "description": self.description,
            "author_name": self.author_name,
            "domain_name": self.domain_name,
            "email": self.email,
            "open_source_license": self.open_source_license,
            "username_type": self.username_type,
            "timezone": self.timezone,
            "windows": "n",
            "editor": "None",
            "use_docker": self.use_docker,
            "postgresql_version": self.postgresql_version,
            "cloud_provider": self.cloud_provider,
            "mail_service": self.mail_service,
            "rest_api": self.rest_api,
            "use_async": self.use_async,
            "frontend_pipeline": self.frontend_pipeline,
            "use_celery": self.use_celery,
            "mail_catcher": self.mail_catcher,
            "use_sentry": self.use_sentry,
            "use_whitenoise": self.use_whitenoise,
            "use_heroku": self.use_heroku,
            "ci_tool": self.ci_tool,
            "keep_local_envs_in_vcs": "n",
            "debug": "n",
        }


def _generate(config: ProjectConfig, output_dir: Path) -> Path:
    try:
        # Imported lazily: importing cookiecutter is slow and only `new` needs it.
        from cookiecutter.main import cookiecutter  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - declared dependency
        msg = "cookiecutter is not installed: pip install django-ai-harness"
        raise ScaffoldError(msg) from exc

    from cookiecutter.exceptions import CookiecutterException  # noqa: PLC0415

    try:
        generated = cookiecutter(
            COOKIECUTTER_TEMPLATE,
            checkout=config.cookiecutter_ref,
            no_input=True,
            extra_context=config.as_cookiecutter_context(),
            output_dir=str(output_dir),
        )
    except CookiecutterException as exc:
        msg = f"cookiecutter-django generation failed: {exc}"
        raise ScaffoldError(msg) from exc
    return Path(generated)


def scaffold(config: ProjectConfig) -> Path:
    """Generate the project into ``config.target`` and return the created path.

    The project is built in a temporary directory and moved into place only once the
    overlay succeeded, so a failure never leaves a half-written tree behind.
    """
    if config.target.exists():
        msg = f"target already exists: {config.target}"
        raise ScaffoldError(msg)

    config.target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="django-ai-harness-"))
    try:
        generated = _generate(config, staging)
        overlay_module.apply(generated, with_pgbouncer=config.with_pgbouncer)
        shutil.move(str(generated), str(config.target))
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return config.target


def next_steps(config: ProjectConfig) -> str:
    """Human-facing instructions printed after a successful generation."""
    translate = Translator(config.language)
    lines = [
        translate("cli.created", path=config.target),
        "",
        f"{translate('cli.next_steps')}:",
        f"  cd {config.target}",
        "  uv sync",
    ]
    if config.use_docker == "y":
        if config.with_pgbouncer:
            lines += [
                "  docker compose -f docker-compose.local.yml "
                "-f docker-compose.pgbouncer.yml up -d",
                "  uv run python manage.py migrate --database=direct",
            ]
        else:
            lines += [
                "  docker compose -f docker-compose.local.yml up -d",
                "  uv run python manage.py migrate",
            ]
    else:
        lines += [f"  {translate('cli.configure_db')}", "  uv run python manage.py migrate"]
    lines.append("  uv run python manage.py runserver")
    return "\n".join(lines)
