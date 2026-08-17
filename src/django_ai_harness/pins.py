"""Pinned upstream references the harness builds on.

Everything the overlay injects into a generated project is resolved from files in
``django_ai_harness/data``. Nothing is resolved from the network at overlay time, which
is what makes regeneration of the golden ``example/`` reproducible.
"""

from __future__ import annotations

import os
import re
from importlib import resources
from pathlib import Path

__all__ = [
    "Requirement",
    "cookiecutter_ref",
    "data_path",
    "dev_requirements",
    "normalize_name",
]

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
_NORMALIZE_RE = re.compile(r"[-_.]+")


def data_path(name: str) -> Path:
    """Return a path inside the packaged ``data/`` directory.

    Works both from a source checkout and from an installed wheel.
    """
    return Path(str(resources.files("django_ai_harness") / "data" / name))


def _first_meaningful_line(text: str) -> str | None:
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            return line
    return None


def cookiecutter_ref() -> str:
    """Resolve the cookiecutter-django git ref to generate from.

    ``COOKIECUTTER_DJANGO_REF`` wins so that CI can intentionally probe upstream tip.
    """
    override = os.environ.get("COOKIECUTTER_DJANGO_REF", "").strip()
    if override:
        return override

    pin_file = data_path("cookiecutter-django.pin")
    ref = _first_meaningful_line(pin_file.read_text(encoding="utf-8"))
    if not ref:
        msg = f"no cookiecutter-django ref found in {pin_file}"
        raise RuntimeError(msg)
    return ref


def normalize_name(requirement: str) -> str:
    """Normalize a requirement to its PEP 503 project name.

    ``"django-stubs[compatible-mypy]==6.0.9"`` -> ``"django-stubs"``
    """
    match = _NAME_RE.match(requirement.strip())
    if not match:
        return requirement.strip().lower()
    return _NORMALIZE_RE.sub("-", match.group(0)).lower()


class Requirement(str):
    """A requirement string that sorts and compares by its normalized project name."""

    __slots__ = ()

    @property
    def name(self) -> str:
        return normalize_name(self)


def dev_requirements() -> list[Requirement]:
    """Return the pinned DX requirements the overlay adds to generated projects."""
    text = data_path("dev-requirements.txt").read_text(encoding="utf-8")
    requirements = [
        Requirement(line.strip())
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    unpinned = [req for req in requirements if "==" not in req]
    if unpinned:
        msg = (
            "dev-requirements.txt must pin every dependency with '==' "
            f"(offenders: {', '.join(unpinned)})"
        )
        raise ValueError(msg)
    return sorted(requirements, key=lambda req: req.name)
