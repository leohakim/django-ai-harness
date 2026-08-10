# Security Policy

## Supported versions

Security fixes are applied on the default branch (`main`) of django-ai-harness.

## Reporting a vulnerability

Please open a **private** GitHub security advisory on this repository, or email the
maintainer listed on the GitHub profile if advisories are unavailable.

Do not open public issues for unfixed vulnerabilities that could put generated
projects at risk.

## Scope notes

- `example/.envs/` contains cookiecutter **placeholders**, not production secrets.
- Generated projects inherit cookiecutter-django’s security posture; review upstream
  docs before deploying.
