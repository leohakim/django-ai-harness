"""Shared non-interactive scaffold used by CLI scripts and the Textual wizard."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_COOKIECUTTER_REF = "cdbe7265c79f43fd3e22c4527a97c8c7a5c72a5b"


def sanitize_slug(raw: str) -> str:
    slug = raw.strip().replace("-", "_").replace(".", "_").replace(" ", "_")
    slug = re.sub(r"[^0-9a-zA-Z_]", "", slug)
    if not slug:
        raise ValueError("El slug no puede quedar vacío")
    if slug[0].isdigit():
        slug = f"p_{slug}"
    if not slug.isidentifier():
        raise ValueError(f"'{slug}' no es un identificador Python válido")
    return slug


@dataclass
class ProjectConfig:
    target: Path
    project_name: str
    description: str = "Project managed with django-ai-harness"
    author_name: str = "django-ai-harness"
    domain_name: str = "example.com"
    email: str = "maintainers@example.com"
    open_source_license: str = "MIT"
    username_type: str = "email"
    timezone: str = "UTC"
    use_docker: str = "y"
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
    cookiecutter_ref: str = field(
        default_factory=lambda: os.environ.get(
            "COOKIECUTTER_DJANGO_REF",
            DEFAULT_COOKIECUTTER_REF,
        )
    )

    def __post_init__(self) -> None:
        self.target = Path(self.target).expanduser().resolve()
        if self.with_pgbouncer:
            self.use_docker = "y"
        if not self.project_slug:
            self.project_slug = sanitize_slug(self.target.name)
        else:
            self.project_slug = sanitize_slug(self.project_slug)


def _require_tools() -> None:
    if shutil.which("cookiecutter") is None:
        raise RuntimeError("cookiecutter no está instalado (brew install cookiecutter)")
    if shutil.which("uv") is None:
        raise RuntimeError("uv no está instalado (https://docs.astral.sh/uv/)")


def scaffold(config: ProjectConfig, harness_root: Path) -> Path:
    """Generate cookiecutter-django + overlay into config.target. Returns target path."""
    _require_tools()
    harness_root = harness_root.resolve()
    if config.target.exists():
        raise FileExistsError(f"El destino ya existe: {config.target}")

    config.target.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="django-ai-harness-"))
    try:
        cmd = [
            "cookiecutter",
            "gh:cookiecutter/cookiecutter-django",
            "--checkout",
            config.cookiecutter_ref,
            "--no-input",
            "--output-dir",
            str(tmp),
            f"project_name={config.project_name}",
            f"project_slug={config.project_slug}",
            f"description={config.description}",
            f"author_name={config.author_name}",
            f"domain_name={config.domain_name}",
            f"email={config.email}",
            f"open_source_license={config.open_source_license}",
            f"username_type={config.username_type}",
            f"timezone={config.timezone}",
            "windows=n",
            "editor=None",
            f"use_docker={config.use_docker}",
            f"cloud_provider={config.cloud_provider}",
            f"mail_service={config.mail_service}",
            f"rest_api={config.rest_api}",
            f"use_async={config.use_async}",
            f"frontend_pipeline={config.frontend_pipeline}",
            f"use_celery={config.use_celery}",
            f"mail_catcher={config.mail_catcher}",
            f"use_sentry={config.use_sentry}",
            f"use_whitenoise={config.use_whitenoise}",
            f"use_heroku={config.use_heroku}",
            f"ci_tool={config.ci_tool}",
            "keep_local_envs_in_vcs=y",
            "debug=n",
        ]
        subprocess.run(cmd, check=True)

        generated = tmp / config.project_slug
        if not generated.is_dir():
            kids = [p for p in tmp.iterdir() if p.is_dir()]
            if len(kids) != 1:
                raise RuntimeError("No se pudo localizar el proyecto generado por cookiecutter")
            generated = kids[0]

        overlay = [
            "python3",
            str(harness_root / "overlay" / "apply.py"),
            str(generated),
            "--harness-root",
            str(harness_root),
        ]
        if config.with_pgbouncer:
            overlay.append("--with-pgbouncer")
        subprocess.run(overlay, check=True)

        shutil.move(str(generated), str(config.target))
        return config.target
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def next_steps(config: ProjectConfig) -> str:
    lines = [
        f"Proyecto listo en: {config.target}",
        "",
        "Siguiente:",
        f"  cd {config.target}",
        "  uv sync",
    ]
    if config.use_docker == "y":
        if config.with_pgbouncer:
            lines.append(
                "  docker compose -f docker-compose.local.yml -f docker-compose.pgbouncer.yml up -d"
            )
            lines.append(
                "  POSTGRES_HOST=postgres POSTGRES_PORT=5432 USE_PGBOUNCER=False "
                "uv run python manage.py migrate"
            )
        else:
            lines.append("  docker compose -f docker-compose.local.yml up -d")
            lines.append("  uv run python manage.py migrate")
    else:
        lines.append("  # Configura POSTGRES_* o DATABASE_URL, luego:")
        lines.append("  uv run python manage.py migrate")
    lines.append("  uv run python manage.py runserver")
    return "\n".join(lines)
