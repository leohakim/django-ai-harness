"""Minimal message catalog for user-facing text.

Only presentation strings are translated. Exceptions raised by library code stay in
English so that tracebacks, bug reports and CI logs are readable by every contributor.

Language resolution order:

1. explicit ``--lang`` argument
2. ``DJANGO_AI_HARNESS_LANG``
3. ``LANG`` / ``LC_ALL`` from the environment
4. English
"""

from __future__ import annotations

import os

__all__ = ["DEFAULT_LANGUAGE", "LANGUAGES", "Translator", "resolve_language"]

DEFAULT_LANGUAGE = "en"
LANGUAGES = ("en", "es")

MESSAGES: dict[str, dict[str, str]] = {
    "wizard.title": {
        "en": "django-ai-harness — new project",
        "es": "django-ai-harness — proyecto nuevo",
    },
    "wizard.subtitle": {
        "en": "cookiecutter-django (pinned) + harness overlay",
        "es": "cookiecutter-django (pineado) + overlay del harness",
    },
    "wizard.identity.title": {"en": "Project identity", "es": "Identidad del proyecto"},
    "wizard.identity.help": {
        "en": (
            "The **slug** is derived from the target directory and must be a valid Python "
            "identifier (`my_shop`, not `my-shop`).\n\n"
            "The harness then runs **cookiecutter-django** and applies the "
            "**django-ai-harness overlay** on top: DX defaults, HackSoft architecture and "
            "an agent contract."
        ),
        "es": (
            "El **slug** se deriva de la carpeta destino y debe ser un identificador Python "
            "válido (`my_shop`, no `my-shop`).\n\n"
            "El harness luego ejecuta **cookiecutter-django** y aplica encima el "
            "**overlay de django-ai-harness**: defaults de DX, arquitectura HackSoft y un "
            "contrato para agentes."
        ),
    },
    "wizard.field.target": {"en": "Target directory", "es": "Carpeta destino"},
    "wizard.field.project_name": {"en": "Project name", "es": "Nombre del proyecto"},
    "wizard.field.author": {"en": "Author", "es": "Autor"},
    "wizard.field.email": {"en": "Email", "es": "Email"},
    "wizard.field.domain": {"en": "Domain", "es": "Dominio"},
    "wizard.section.adds": {"en": "Adds", "es": "Agrega"},
    "wizard.section.removes": {"en": "Leaves out", "es": "Deja fuera"},
    "wizard.section.implication": {"en": "Implication", "es": "Implicancia"},
    "wizard.section.why": {"en": "Why this matters", "es": "Por qué importa"},
    "wizard.button.back": {"en": "Back", "es": "Atrás"},
    "wizard.button.next": {"en": "Next", "es": "Siguiente"},
    "wizard.button.create": {"en": "Create project", "es": "Crear proyecto"},
    "wizard.button.quit": {"en": "Quit", "es": "Salir"},
    "wizard.summary.title": {"en": "Review", "es": "Revisión"},
    "wizard.summary.intro": {
        "en": "The harness will generate the project with these choices:",
        "es": "El harness generará el proyecto con estas elecciones:",
    },
    "wizard.running": {"en": "Generating project…", "es": "Generando proyecto…"},
    "wizard.done": {"en": "Project created", "es": "Proyecto creado"},
    "wizard.failed": {"en": "Generation failed", "es": "Falló la generación"},
    "wizard.step": {"en": "Step {current} of {total}", "es": "Paso {current} de {total}"},
    "cli.next_steps": {"en": "Next steps", "es": "Siguientes pasos"},
    "cli.configure_db": {
        "en": "# Provide POSTGRES_* or DATABASE_URL, then:",
        "es": "# Configura POSTGRES_* o DATABASE_URL, luego:",
    },
    "cli.created": {"en": "Project ready at: {path}", "es": "Proyecto listo en: {path}"},
}


def resolve_language(explicit: str | None = None) -> str:
    """Pick the UI language from an explicit flag or the environment."""
    candidates = [
        explicit,
        os.environ.get("DJANGO_AI_HARNESS_LANG"),
        os.environ.get("LC_ALL"),
        os.environ.get("LANG"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        code = candidate.strip().lower().replace("-", "_").split(".")[0].split("_")[0]
        if code in LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


class Translator:
    """Look up presentation strings for one language, falling back to English."""

    __slots__ = ("language",)

    def __init__(self, language: str | None = None) -> None:
        self.language = resolve_language(language)

    def __call__(self, key: str, **kwargs: object) -> str:
        entry = MESSAGES.get(key)
        if entry is None:
            return key
        template = entry.get(self.language) or entry[DEFAULT_LANGUAGE]
        return template.format(**kwargs) if kwargs else template

    def pick(self, value: str | dict[str, str]) -> str:
        """Resolve a possibly-localized value coming from a data catalog."""
        if isinstance(value, str):
            return value
        return value.get(self.language) or value[DEFAULT_LANGUAGE]
