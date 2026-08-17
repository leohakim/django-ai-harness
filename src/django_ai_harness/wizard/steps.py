"""Decision catalog for the guided wizard.

Every string is a ``{"en": ..., "es": ...}`` mapping resolved through
:class:`django_ai_harness.i18n.Translator`. Technical labels (Docker, DRF, Celery) stay
in English in both languages because that is how the ecosystem names them.

Each choice states what it *adds*, what it *leaves out*, and the practical implication,
so the wizard teaches the trade-off instead of just collecting an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

__all__ = ["DECISIONS", "Choice", "Decision", "Text", "visible_decisions"]

Text = dict[str, str]


@dataclass(frozen=True)
class Choice:
    value: str
    label: Text
    adds: Text
    removes: Text
    implication: Text


@dataclass(frozen=True)
class Decision:
    key: str
    title: Text
    subtitle: Text
    why: Text
    choices: tuple[Choice, ...]
    default: str
    #: Only shown when every ``(key, value)`` pair matches the answers so far.
    requires: tuple[tuple[str, str], ...] = field(default=())


def visible_decisions(answers: dict[str, str]) -> list[Decision]:
    """Filter the catalog down to the decisions that apply to the current answers."""
    return [
        decision
        for decision in DECISIONS
        if all(answers.get(key) == expected for key, expected in decision.requires)
    ]


DECISIONS: tuple[Decision, ...] = (
    Decision(
        key="use_docker",
        title={"en": "Docker Compose", "es": "Docker Compose"},
        subtitle={
            "en": "Do you want a containerized local environment?",
            "es": "¿Querés un entorno local con contenedores?",
        },
        why={
            "en": (
                "cookiecutter-django can generate `docker-compose.local.yml` with "
                "**PostgreSQL**, Redis (when Celery is enabled) and the **django** service "
                "ready for `up -d`.\n\nWithout Docker you provide PostgreSQL yourself via "
                "`POSTGRES_*` or `DATABASE_URL`."
            ),
            "es": (
                "cookiecutter-django puede generar `docker-compose.local.yml` con "
                "**PostgreSQL**, Redis (si activás Celery) y el servicio **django** listo para "
                "`up -d`.\n\nSin Docker tenés que proveer PostgreSQL vos mismo con "
                "`POSTGRES_*` o `DATABASE_URL`."
            ),
        },
        default="y",
        choices=(
            Choice(
                value="y",
                label={
                    "en": "Yes — use Docker Compose (recommended)",
                    "es": "Sí — usar Docker Compose (recomendado)",
                },
                adds={
                    "en": "Local Compose stack, postgres service, one-command startup",
                    "es": "Stack Compose local, servicio postgres, arranque de un comando",
                },
                removes={
                    "en": "Nothing critical; adds a dependency on Docker Engine",
                    "es": "Nada crítico; agrega una dependencia de Docker Engine",
                },
                implication={
                    "en": "A reproducible environment. The quickstart assumes this path.",
                    "es": "Un entorno reproducible. El quickstart asume este camino.",
                },
            ),
            Choice(
                value="n",
                label={"en": "No — without Docker", "es": "No — sin Docker"},
                adds={"en": "A lighter template on disk", "es": "Una plantilla más liviana"},
                removes={
                    "en": "Compose, bundled PostgreSQL, the guided one-command path",
                    "es": "Compose, PostgreSQL empaquetado, el camino guiado de un comando",
                },
                implication={
                    "en": "Useful when you already run PostgreSQL. Export env vars before migrating.",
                    "es": "Útil si ya tenés PostgreSQL. Exportá las variables antes de migrar.",
                },
            ),
        ),
    ),
    Decision(
        key="rest_api",
        title={"en": "HTTP API", "es": "API HTTP"},
        subtitle={"en": "Which API stack?", "es": "¿Qué stack de API?"},
        why={
            "en": (
                "The harness recommends **DRF** because it matches the **HackSoft** contract "
                "(thin APIs with nested input/output serializers). **Django Ninja** is more "
                "typed and modern; **None** leaves plain views and templates."
            ),
            "es": (
                "El harness recomienda **DRF** porque encaja con el contrato **HackSoft** "
                "(APIs finas con serializers anidados de entrada/salida). **Django Ninja** es "
                "más tipado y moderno; **None** deja solo vistas y templates."
            ),
        },
        default="DRF",
        choices=(
            Choice(
                value="DRF",
                label={
                    "en": "DRF — Django REST Framework (recommended)",
                    "es": "DRF — Django REST Framework (recomendado)",
                },
                adds={
                    "en": "djangorestframework, drf-spectacular, HackSoft API patterns",
                    "es": "djangorestframework, drf-spectacular, patrones de API HackSoft",
                },
                removes={
                    "en": "Nothing, if you plan to serve JSON",
                    "es": "Nada, si planeás servir JSON",
                },
                implication={
                    "en": "Best supported by the harness skills and the app skeleton.",
                    "es": "Es lo mejor soportado por los skills y el esqueleto de app.",
                },
            ),
            Choice(
                value="Django Ninja",
                label={"en": "Django Ninja", "es": "Django Ninja"},
                adds={
                    "en": "Typed API with Pydantic, less boilerplate",
                    "es": "API tipada con Pydantic, menos boilerplate",
                },
                removes={
                    "en": "The DRF patterns the styleguide and skeleton assume",
                    "es": "Los patrones DRF que asumen el styleguide y el esqueleto",
                },
                implication={
                    "en": "Excellent typed DX; you will adapt the API layer of the skeleton.",
                    "es": "Excelente DX tipado; vas a adaptar la capa de API del esqueleto.",
                },
            ),
            Choice(
                value="None",
                label={"en": "None — no API framework", "es": "None — sin framework de API"},
                adds={"en": "Fewer dependencies", "es": "Menos dependencias"},
                removes={
                    "en": "DRF/Ninja and OpenAPI out of the box",
                    "es": "DRF/Ninja y OpenAPI listos para usar",
                },
                implication={
                    "en": "Ideal for server-rendered apps. You can add an API later.",
                    "es": "Ideal para apps server-rendered. Podés agregar una API después.",
                },
            ),
        ),
    ),
    Decision(
        key="use_celery",
        title={"en": "Celery", "es": "Celery"},
        subtitle={
            "en": "Do you need background jobs?",
            "es": "¿Necesitás trabajos en segundo plano?",
        },
        why={
            "en": (
                "**Celery** runs work outside the request cycle (emails, imports, webhooks). "
                "Locally it comes with **Redis** through Compose."
            ),
            "es": (
                "**Celery** ejecuta trabajo fuera del ciclo de request (emails, imports, "
                "webhooks). En local viene con **Redis** vía Compose."
            ),
        },
        default="n",
        choices=(
            Choice(
                value="n",
                label={
                    "en": "No — skip Celery for now (recommended)",
                    "es": "No — sin Celery por ahora (recomendado)",
                },
                adds={"en": "Fewer services to operate", "es": "Menos servicios que operar"},
                removes={
                    "en": "A task queue from day one",
                    "es": "Una cola de tareas desde el día 1",
                },
                implication={
                    "en": "Perfect for MVPs and synchronous APIs; easy to add later.",
                    "es": "Perfecto para MVPs y APIs síncronas; fácil de agregar después.",
                },
            ),
            Choice(
                value="y",
                label={"en": "Yes — include Celery", "es": "Sí — incluir Celery"},
                adds={
                    "en": "Celery workers, Redis broker, async task wiring",
                    "es": "Workers Celery, broker Redis, cableado de tareas async",
                },
                removes={
                    "en": "The minimal-stack simplicity",
                    "es": "La simplicidad del stack mínimo",
                },
                implication={
                    "en": "Turn it on when you already know jobs are coming.",
                    "es": "Activalo cuando ya sabés que va a haber jobs.",
                },
            ),
        ),
    ),
    Decision(
        key="frontend_pipeline",
        title={"en": "Frontend pipeline", "es": "Pipeline de frontend"},
        subtitle={
            "en": "How will you build static CSS/JS?",
            "es": "¿Cómo vas a construir CSS/JS estáticos?",
        },
        why={
            "en": (
                "cookiecutter-django can wire **Webpack**, **Gulp** or **Django Compressor**. "
                "If your UI is minimal, **None** keeps Node out of the scaffold."
            ),
            "es": (
                "cookiecutter-django puede cablear **Webpack**, **Gulp** o **Django Compressor**. "
                "Si tu UI es mínima, **None** mantiene Node fuera del scaffold."
            ),
        },
        default="None",
        choices=(
            Choice(
                value="None",
                label={
                    "en": "None — no Node pipeline (recommended)",
                    "es": "None — sin pipeline Node (recomendado)",
                },
                adds={
                    "en": "Less tooling; plain static files",
                    "es": "Menos tooling; estáticos simples",
                },
                removes={"en": "A bundled JS/CSS build", "es": "Un build empaquetado de JS/CSS"},
                implication={
                    "en": "You can add Vite or Webpack later without fighting the template.",
                    "es": "Podés agregar Vite o Webpack después sin pelear con la plantilla.",
                },
            ),
            Choice(
                value="Webpack",
                label={"en": "Webpack", "es": "Webpack"},
                adds={
                    "en": "Modern JS/CSS bundling in-project",
                    "es": "Bundling moderno de JS/CSS",
                },
                removes={"en": "Simplicity; you need Node", "es": "Simplicidad; necesitás Node"},
                implication={
                    "en": "Useful when the frontend lives in the same repository.",
                    "es": "Útil cuando el frontend vive en el mismo repositorio.",
                },
            ),
            Choice(
                value="Gulp",
                label={"en": "Gulp", "es": "Gulp"},
                adds={"en": "Classic asset tasks", "es": "Tasks clásicas de assets"},
                removes={"en": "A more contemporary bundler", "es": "Un bundler más contemporáneo"},
                implication={
                    "en": "Only if your team already depends on Gulp.",
                    "es": "Solo si tu equipo ya depende de Gulp.",
                },
            ),
            Choice(
                value="Django Compressor",
                label={"en": "Django Compressor", "es": "Django Compressor"},
                adds={
                    "en": "Static compression inside Django",
                    "es": "Compresión de estáticos en Django",
                },
                removes={"en": "A full JS bundler", "es": "Un bundler JS completo"},
                implication={
                    "en": "Good for light CSS/JS without a mandatory Node build.",
                    "es": "Bueno para CSS/JS livianos sin un build Node obligatorio.",
                },
            ),
        ),
    ),
    Decision(
        key="ci_tool",
        title={"en": "Continuous integration", "es": "Integración continua"},
        subtitle={"en": "Which CI should be generated?", "es": "¿Qué CI generamos?"},
        why={
            "en": "The template ships a ready pipeline. **Github** fits repositories on GitHub Actions.",
            "es": "La plantilla trae un pipeline listo. **Github** encaja con repos en GitHub Actions.",
        },
        default="Github",
        choices=(
            Choice(
                value="Github",
                label={"en": "GitHub Actions (recommended)", "es": "GitHub Actions (recomendado)"},
                adds={
                    "en": "A CI workflow under `.github/`",
                    "es": "Un workflow de CI en `.github/`",
                },
                removes={"en": "Nothing if you use GitHub", "es": "Nada si usás GitHub"},
                implication={
                    "en": "Lint and tests run from the first push.",
                    "es": "Lint y tests corren desde el primer push.",
                },
            ),
            Choice(
                value="Gitlab",
                label={"en": "GitLab CI", "es": "GitLab CI"},
                adds={"en": "A GitLab CI configuration", "es": "Una configuración de GitLab CI"},
                removes={"en": "GitHub Actions", "es": "GitHub Actions"},
                implication={
                    "en": "Pick this only when the remote is GitLab.",
                    "es": "Elegí esto solo si el remoto es GitLab.",
                },
            ),
            Choice(
                value="None",
                label={"en": "None — no CI in the template", "es": "None — sin CI en la plantilla"},
                adds={
                    "en": "A cleaner repository at the start",
                    "es": "Un repo más limpio al inicio",
                },
                removes={"en": "The generated pipeline", "es": "El pipeline generado"},
                implication={
                    "en": "You will add CI manually.",
                    "es": "Vas a agregar CI manualmente.",
                },
            ),
        ),
    ),
    Decision(
        key="use_whitenoise",
        title={"en": "WhiteNoise", "es": "WhiteNoise"},
        subtitle={
            "en": "Serve static files from the app server?",
            "es": "¿Servir estáticos desde el app server?",
        },
        why={
            "en": (
                "**WhiteNoise** serves static files without a dedicated Nginx in many simple "
                "deployments. With a CDN or object storage you may not need it."
            ),
            "es": (
                "**WhiteNoise** sirve estáticos sin un Nginx dedicado en muchos deploys simples. "
                "Con un CDN u object storage puede que no lo necesites."
            ),
        },
        default="y",
        choices=(
            Choice(
                value="y",
                label={
                    "en": "Yes — WhiteNoise (recommended)",
                    "es": "Sí — WhiteNoise (recomendado)",
                },
                adds={
                    "en": "Robust static serving on PaaS and simple hosting",
                    "es": "Estáticos robustos en PaaS y hosting simple",
                },
                removes={"en": "Nothing in practice", "es": "Nada en la práctica"},
                implication={
                    "en": "A good default; complement it with a CDN later.",
                    "es": "Un buen default; complementalo con un CDN después.",
                },
            ),
            Choice(
                value="n",
                label={"en": "No — without WhiteNoise", "es": "No — sin WhiteNoise"},
                adds={"en": "One less middleware", "es": "Un middleware menos"},
                removes={"en": "Out-of-the-box static serving", "es": "Serving de estáticos listo"},
                implication={
                    "en": "Use when a reverse proxy or CDN owns `/static/`.",
                    "es": "Usalo cuando un reverse proxy o CDN se encarga de `/static/`.",
                },
            ),
        ),
    ),
    Decision(
        key="use_sentry",
        title={"en": "Sentry", "es": "Sentry"},
        subtitle={"en": "Include error monitoring?", "es": "¿Incluir monitoreo de errores?"},
        why={
            "en": "**Sentry** captures production exceptions. It needs an account and a DSN.",
            "es": "**Sentry** captura excepciones en producción. Necesita una cuenta y un DSN.",
        },
        default="n",
        choices=(
            Choice(
                value="n",
                label={
                    "en": "No — skip Sentry for now (recommended)",
                    "es": "No — sin Sentry por ahora (recomendado)",
                },
                adds={"en": "Fewer secrets to manage", "es": "Menos secretos que gestionar"},
                removes={"en": "Ready-made error tracking", "es": "Error tracking listo"},
                implication={
                    "en": "Add it when you have a production environment.",
                    "es": "Agregalo cuando tengas un entorno de producción.",
                },
            ),
            Choice(
                value="y",
                label={"en": "Yes — wire Sentry", "es": "Sí — cablear Sentry"},
                adds={
                    "en": "Sentry hooks and configuration",
                    "es": "Hooks y configuración de Sentry",
                },
                removes={"en": "A shorter onboarding", "es": "Un onboarding más corto"},
                implication={
                    "en": "You will need to set the DSN in environment variables.",
                    "es": "Vas a necesitar configurar el DSN en variables de entorno.",
                },
            ),
        ),
    ),
    Decision(
        key="cloud_provider",
        title={"en": "Cloud provider", "es": "Proveedor cloud"},
        subtitle={"en": "Cloud storage for media?", "es": "¿Storage cloud para media?"},
        why={
            "en": (
                "The template can wire media backends for **AWS**, **GCP** or **Azure**. "
                "**None** avoids cloud credentials at the start."
            ),
            "es": (
                "La plantilla puede cablear backends de media para **AWS**, **GCP** o **Azure**. "
                "**None** evita credenciales cloud al inicio."
            ),
        },
        default="None",
        choices=(
            Choice(
                value="None",
                label={
                    "en": "None — no cloud storage (recommended)",
                    "es": "None — sin storage cloud (recomendado)",
                },
                adds={"en": "Fewer secrets", "es": "Menos secretos"},
                removes={"en": "Cloud media from day one", "es": "Media en cloud desde el día 1"},
                implication={
                    "en": "Local media for development; add cloud when you deploy for real.",
                    "es": "Media local para desarrollo; agregá cloud cuando deploys en serio.",
                },
            ),
            Choice(
                value="AWS",
                label={"en": "AWS", "es": "AWS"},
                adds={"en": "S3 media integration", "es": "Integración de media con S3"},
                removes={"en": "Local simplicity", "es": "Simplicidad local"},
                implication={
                    "en": "You will need AWS credentials.",
                    "es": "Vas a necesitar credenciales AWS.",
                },
            ),
            Choice(
                value="GCP",
                label={"en": "GCP", "es": "GCP"},
                adds={
                    "en": "Google Cloud Storage integration",
                    "es": "Integración con Google Cloud Storage",
                },
                removes={"en": "Local simplicity", "es": "Simplicidad local"},
                implication={
                    "en": "You will need a GCP project and credentials.",
                    "es": "Vas a necesitar un proyecto GCP y credenciales.",
                },
            ),
            Choice(
                value="Azure",
                label={"en": "Azure", "es": "Azure"},
                adds={"en": "Azure Storage integration", "es": "Integración con Azure Storage"},
                removes={"en": "Local simplicity", "es": "Simplicidad local"},
                implication={
                    "en": "You will need Azure resources provisioned.",
                    "es": "Vas a necesitar recursos Azure aprovisionados.",
                },
            ),
        ),
    ),
    Decision(
        key="with_pgbouncer",
        title={"en": "PgBouncer", "es": "PgBouncer"},
        subtitle={
            "en": "Connection pooling? (the engine stays PostgreSQL)",
            "es": "¿Pool de conexiones? (el motor sigue siendo PostgreSQL)",
        },
        why={
            "en": (
                "**PgBouncer** cuts memory use when you run many workers. The harness ships it "
                "opt-in: Compose templates plus `USE_PGBOUNCER`-gated settings and a `direct` "
                "database alias for migrations. It only makes sense with Docker Compose."
            ),
            "es": (
                "**PgBouncer** reduce el uso de memoria cuando corrés muchos workers. El harness "
                "lo trae opt-in: plantillas Compose más settings gateados por `USE_PGBOUNCER` y un "
                "alias `direct` para migraciones. Solo tiene sentido con Docker Compose."
            ),
        },
        default="n",
        requires=(("use_docker", "y"),),
        choices=(
            Choice(
                value="n",
                label={
                    "en": "No — direct PostgreSQL (recommended to start)",
                    "es": "No — PostgreSQL directo (recomendado al inicio)",
                },
                adds={
                    "en": "A simple topology: app to postgres",
                    "es": "Topología simple: app a postgres",
                },
                removes={"en": "The extra pooler service", "es": "El servicio extra del pooler"},
                implication={
                    "en": "Ideal locally and for projects without connection pressure.",
                    "es": "Ideal en local y para proyectos sin presión de conexiones.",
                },
            ),
            Choice(
                value="y",
                label={"en": "Yes — enable PgBouncer", "es": "Sí — activar PgBouncer"},
                adds={
                    "en": "pgbouncer service, USE_PGBOUNCER envs, a `direct` alias for DDL",
                    "es": "Servicio pgbouncer, envs USE_PGBOUNCER, alias `direct` para DDL",
                },
                removes={
                    "en": "The direct app-to-postgres runtime connection",
                    "es": "La conexión directa app-postgres en runtime",
                },
                implication={
                    "en": "Use on hosts with many workers. Migrate with `--database=direct`.",
                    "es": "Usalo en hosts con muchos workers. Migrá con `--database=direct`.",
                },
            ),
        ),
    ),
)
