"""Command line interface.

django-ai-harness new <dir> "<Name>"   generate a project (non-interactive)
django-ai-harness wizard               guided TUI for the same thing
django-ai-harness apply <dir>          apply or upgrade the overlay in place
django-ai-harness info                 show pinned upstream versions
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from django_ai_harness import OVERLAY_VERSION
from django_ai_harness import __version__
from django_ai_harness import overlay as overlay_module
from django_ai_harness.i18n import LANGUAGES
from django_ai_harness.i18n import resolve_language
from django_ai_harness.pins import cookiecutter_ref
from django_ai_harness.pins import dev_requirements
from django_ai_harness.scaffold import ProjectConfig
from django_ai_harness.scaffold import ScaffoldError
from django_ai_harness.scaffold import next_steps
from django_ai_harness.scaffold import scaffold

__all__ = ["main"]

_BOOL_CHOICES = ("y", "n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="django-ai-harness",
        description=(
            "Bootstrap Django projects with strong developer experience, HackSoft "
            "architecture, and instructions AI agents can follow."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  uvx django-ai-harness new ~/Projects/my_shop "My Shop"\n'
            "  uvx django-ai-harness wizard\n"
            "  uvx django-ai-harness apply . --check\n"
        ),
    )
    parser.add_argument("--version", action="version", version=f"django-ai-harness {__version__}")
    parser.add_argument(
        "--lang",
        choices=LANGUAGES,
        help="UI language for interactive output (default: from the environment).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new = subparsers.add_parser("new", help="Generate a new Django project (non-interactive).")
    new.add_argument("target", type=Path, help="Directory to create, e.g. ~/Projects/my_shop")
    new.add_argument("project_name", nargs="?", default=None, help="Human-readable project name")
    new.add_argument(
        "--slug", default="", help="Python package name (default: derived from target)"
    )
    new.add_argument("--author-name", default="django-ai-harness")
    new.add_argument("--email", default="")
    new.add_argument("--domain-name", default="example.com")
    new.add_argument("--description", default="Project managed with django-ai-harness")
    new.add_argument("--use-docker", choices=_BOOL_CHOICES, default="y")
    new.add_argument("--rest-api", choices=("DRF", "Django Ninja", "None"), default="DRF")
    new.add_argument("--use-celery", choices=_BOOL_CHOICES, default="n")
    new.add_argument(
        "--frontend-pipeline",
        choices=("None", "Webpack", "Gulp", "Django Compressor"),
        default="None",
    )
    new.add_argument("--ci-tool", choices=("Github", "Gitlab", "None"), default="Github")
    new.add_argument("--use-whitenoise", choices=_BOOL_CHOICES, default="y")
    new.add_argument("--use-sentry", choices=_BOOL_CHOICES, default="n")
    new.add_argument("--cloud-provider", choices=("None", "AWS", "GCP", "Azure"), default="None")
    new.add_argument("--timezone", default="UTC")
    new.add_argument(
        "--with-pgbouncer", action="store_true", help="Enable PgBouncer (implies Docker)"
    )

    wizard = subparsers.add_parser("wizard", help="Guided TUI for creating a project.")
    wizard.add_argument("--target", type=Path, default=None, help="Pre-fill the target directory")

    apply_cmd = subparsers.add_parser("apply", help="Apply or upgrade the overlay in a project.")
    apply_cmd.add_argument("project_root", type=Path, help="Path to an existing Django project")
    apply_cmd.add_argument("--with-pgbouncer", action="store_true")
    apply_cmd.add_argument(
        "--force",
        action="store_true",
        help="Overwrite every file the overlay owns, including locally edited ones",
    )
    apply_cmd.add_argument(
        "--check", action="store_true", help="Report drift and exit 1; writes nothing"
    )

    subparsers.add_parser("info", help="Show the pinned upstream versions this harness uses.")
    return parser


def _cmd_new(args: argparse.Namespace, language: str) -> int:
    config = ProjectConfig(
        target=args.target,
        project_name=args.project_name or args.target.name.replace("_", " ").title(),
        project_slug=args.slug,
        description=args.description,
        author_name=args.author_name,
        domain_name=args.domain_name,
        email=args.email,
        use_docker=args.use_docker,
        rest_api=args.rest_api,
        use_celery=args.use_celery,
        frontend_pipeline=args.frontend_pipeline,
        ci_tool=args.ci_tool,
        use_whitenoise=args.use_whitenoise,
        use_sentry=args.use_sentry,
        cloud_provider=args.cloud_provider,
        timezone=args.timezone,
        with_pgbouncer=args.with_pgbouncer,
        language=language,
    )
    ref = config.cookiecutter_ref[:12]
    print(f"==> Generating {config.project_slug} from cookiecutter-django @ {ref}")
    scaffold(config)
    print()
    print(next_steps(config))
    return 0


def _cmd_wizard(args: argparse.Namespace, language: str) -> int:
    try:
        # Imported here so Textual stays an optional extra for non-interactive users.
        from django_ai_harness.wizard.app import run  # noqa: PLC0415
    except ImportError:
        print(
            "error: the guided wizard needs Textual.\n"
            "  uvx --with textual django-ai-harness wizard\n"
            "  # or: pip install 'django-ai-harness[wizard]'",
            file=sys.stderr,
        )
        return 2
    return run(language=language, target=args.target)


def _cmd_apply(args: argparse.Namespace, _language: str) -> int:
    argv = [str(args.project_root)]
    if args.with_pgbouncer:
        argv.append("--with-pgbouncer")
    if args.force:
        argv.append("--force")
    if args.check:
        argv.append("--check")
    return overlay_module.main(argv)


def _cmd_info(_args: argparse.Namespace, _language: str) -> int:
    print(f"django-ai-harness   {__version__}")
    print(f"overlay contract    {OVERLAY_VERSION}")
    print(f"cookiecutter-django {cookiecutter_ref()}")
    print("\nDX dependencies added to generated projects:")
    for requirement in dev_requirements():
        print(f"  {requirement}")
    return 0


#: Every handler takes (namespace, language) so dispatch stays uniform.
_COMMANDS: dict[str, Callable[[argparse.Namespace, str], int]] = {
    "new": _cmd_new,
    "wizard": _cmd_wizard,
    "apply": _cmd_apply,
    "info": _cmd_info,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    handler = _COMMANDS.get(args.command)
    if handler is None:  # pragma: no cover - argparse rejects unknown commands first
        parser.error(f"unknown command: {args.command}")

    try:
        return handler(args, resolve_language(args.lang))
    except (ScaffoldError, overlay_module.OverlayError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # pragma: no cover - interactive
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
