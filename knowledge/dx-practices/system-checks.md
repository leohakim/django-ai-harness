# System checks

- Run `manage.py check` in CI and before releases.
- Use **django-version-checks** to assert Python/Django versions in deployed environments.
- Add project-specific checks sparingly for invariants that are easy to violate and hard to see in tests.
- Silence checks only with documented justification.
