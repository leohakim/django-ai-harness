# Security Policy

## Supported versions

Security fixes land on the default branch (`main`) and are released from there. Only the
latest published version is supported.

## Reporting a vulnerability

Please [open a private security advisory](https://github.com/leohakim/django-ai-harness/security/advisories/new).
If advisories are unavailable to you, email the maintainer listed on the GitHub profile.

Do not open a public issue for an unfixed vulnerability: this harness writes files into
other people's projects, so a disclosed-but-unfixed issue puts them at risk.

Expect an acknowledgement within a week.

## Scope

**In scope**

- The overlay writing outside the target project directory, or overwriting files it does
  not own.
- Code execution triggered by generating a project with attacker-influenced input
  (project name, slug, description, domain).
- Insecure defaults in the templates the overlay installs — for example the PgBouncer
  Compose fragment exposing the pooler beyond loopback.
- Credentials or secrets committed to this repository.

**Out of scope**

- Vulnerabilities in cookiecutter-django itself. Report those
  [upstream](https://github.com/cookiecutter/cookiecutter-django/security).
- Vulnerabilities in third-party packages the overlay pins. Report those to the package,
  then open an issue here so the pin can be bumped.
- The security posture of a project *you* deployed. Generated projects inherit
  cookiecutter-django's defaults; review its deployment documentation before going live.

## Notes for users

- The golden `example/` is generated with `keep_local_envs_in_vcs=n`, so `.envs/` is
  **not** committed to this repository. Nothing under `example/` contains credentials,
  real or placeholder.
- Generated projects keep their secrets in `.envs/`, which their own `.gitignore`
  excludes. Verify this before your first push.
- The overlay is hermetic: it performs no network access. `django-ai-harness new` does
  reach GitHub to fetch the cookiecutter template, at the exact commit recorded in
  `src/django_ai_harness/data/cookiecutter-django.pin`.
