#!/usr/bin/env python3
"""CLI entrypoint wrapping lib.scaffold for non-interactive use."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib.scaffold import ProjectConfig
from lib.scaffold import next_steps
from lib.scaffold import scaffold

HARNESS_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Non-interactive django-ai-harness scaffold")
    parser.add_argument("--target", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--use-docker", default="y")
    parser.add_argument("--rest-api", default="DRF")
    parser.add_argument("--use-celery", default="n")
    parser.add_argument("--frontend-pipeline", default="None")
    parser.add_argument("--ci-tool", default="Github")
    parser.add_argument("--use-whitenoise", default="y")
    parser.add_argument("--use-sentry", default="n")
    parser.add_argument("--cloud-provider", default="None")
    parser.add_argument("--with-pgbouncer", action="store_true")
    parser.add_argument("--description", default="Project managed with django-ai-harness")
    parser.add_argument("--author-name", default="django-ai-harness")
    parser.add_argument("--domain-name", default="example.com")
    args = parser.parse_args()

    cfg = ProjectConfig(
        target=Path(args.target),
        project_name=args.project_name,
        description=args.description,
        author_name=args.author_name,
        domain_name=args.domain_name,
        email=f"maintainers@{args.domain_name}",
        use_docker=args.use_docker,
        rest_api=args.rest_api,
        use_celery=args.use_celery,
        frontend_pipeline=args.frontend_pipeline,
        ci_tool=args.ci_tool,
        use_whitenoise=args.use_whitenoise,
        use_sentry=args.use_sentry,
        cloud_provider=args.cloud_provider,
        with_pgbouncer=args.with_pgbouncer,
    )
    print(f"==> Scaffolding into {cfg.target}")
    scaffold(cfg, HARNESS_ROOT)
    print(next_steps(cfg))


if __name__ == "__main__":
    main()
