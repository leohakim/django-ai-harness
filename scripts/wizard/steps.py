"""Copy for guided wizard steps (Spanish UI + English technical labels)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    value: str
    label: str
    adds: str
    removes: str
    implication: str


@dataclass(frozen=True)
class Decision:
    key: str
    title: str
    subtitle: str
    why: str
    choices: tuple[Choice, ...]
    default: str
    # If set, this decision is only shown when predicate matches answers so far
    requires: tuple[tuple[str, str], ...] = ()


IDENTITY_HELP = """\
Definimos la identidad del proyecto. El **slug** se deriva del nombre de carpeta
y debe ser un identificador Python válido (`my_shop`, no `my-shop`).

El harness luego aplica **cookiecutter-django** (plantilla upstream) + el **overlay**
de django-ai-harness (DX, HackSoft, herramientas modernas).
"""

DECISIONS: tuple[Decision, ...] = (
    Decision(
        key="use_docker",
        title="Docker / Docker Compose",
        subtitle="¿Quieres entorno local con contenedores?",
        why=(
            "cookiecutter-django puede generar `docker-compose.local.yml` con "
            "**PostgreSQL**, Redis (si Celery), y el servicio **django** listos para `up -d`.\n\n"
            "Sin Docker tendrás que proveer Postgres tú mismo (`POSTGRES_*` / `DATABASE_URL`)."
        ),
        default="y",
        choices=(
            Choice(
                value="y",
                label="Sí — usar Docker Compose (recomendado)",
                adds="Compose local, servicio postgres, flujo `docker compose up -d`",
                removes="Nada crítico; añade dependencia de Docker Desktop/Engine",
                implication=(
                    "Ganas un entorno reproducible. El quickstart del harness asume este camino. "
                    "Necesitas Docker instalado."
                ),
            ),
            Choice(
                value="n",
                label="No — sin Docker",
                adds="Proyecto más liviano en disco de plantilla",
                removes="Compose, Postgres empaquetado, path guiado con un comando",
                implication=(
                    "Útil si ya tienes Postgres. Deberás exportar variables de entorno "
                    "antes de `migrate`."
                ),
            ),
        ),
    ),
    Decision(
        key="rest_api",
        title="API HTTP",
        subtitle="¿Qué stack de API quieres?",
        why=(
            "El harness recomienda **DRF** porque encaja con la arquitectura **HackSoft** "
            "(APIs finas + serializers de entrada/salida). "
            "**Django Ninja** es más tipado/moderno; **None** deja solo vistas/templates."
        ),
        default="DRF",
        choices=(
            Choice(
                value="DRF",
                label="DRF — Django REST Framework (recomendado)",
                adds="djangorestframework, drf-spectacular, patrones API HackSoft",
                removes="Nada si planeas JSON APIs",
                implication="Mejor opción para agentes y APIs versionadas/documentadas.",
            ),
            Choice(
                value="Django Ninja",
                label="Django Ninja",
                adds="API tipada con Pydantic, menos boilerplate DRF",
                removes="Patrones DRF del styleguide (habrá que adaptar skills)",
                implication="Excelente DX tipado; el skill HackSoft asume DRF por defecto.",
            ),
            Choice(
                value="None",
                label="None — sin framework de API",
                adds="Menos dependencias",
                removes="DRF/Ninja, OpenAPI out-of-the-box",
                implication="Ideal para apps solo server-rendered. Puedes añadir API después.",
            ),
        ),
    ),
    Decision(
        key="use_celery",
        title="Celery",
        subtitle="¿Necesitas tareas asíncronas / background jobs?",
        why=(
            "**Celery** ejecuta trabajo fuera del request (emails, imports, webhooks). "
            "En local suele ir con **Redis** vía Compose."
        ),
        default="n",
        choices=(
            Choice(
                value="y",
                label="Sí — incluir Celery",
                adds="Workers Celery, broker Redis (con Docker), tareas async",
                removes="Simplicidad del stack mínimo",
                implication=(
                    "Actívalo si ya sabes que habrá jobs. Si no, empieza sin él "
                    "(fácil de añadir luego)."
                ),
            ),
            Choice(
                value="n",
                label="No — sin Celery (recomendado al inicio)",
                adds="Menos servicios que operar",
                removes="Cola de tareas lista desde el día 1",
                implication="Perfecto para MVPs y APIs síncronas.",
            ),
        ),
    ),
    Decision(
        key="frontend_pipeline",
        title="Frontend pipeline",
        subtitle="¿Cómo construirás CSS/JS estáticos?",
        why=(
            "cookiecutter-django puede cablear **Webpack**, **Gulp** o **Django Compressor**. "
            "Si tu UI es mínima o usas CDN, **None** evita Node en el scaffold."
        ),
        default="None",
        choices=(
            Choice(
                value="None",
                label="None — sin pipeline Node (recomendado)",
                adds="Menos tooling; estáticos simples",
                removes="Build de JS/CSS empaquetado",
                implication="Puedes añadir Vite/Webpack después sin pelear con la plantilla.",
            ),
            Choice(
                value="Webpack",
                label="Webpack",
                adds="Bundling moderno JS/CSS en el proyecto",
                removes="Simplicidad; necesitas Node",
                implication="Útil si el frontend vive en el mismo repo Django.",
            ),
            Choice(
                value="Gulp",
                label="Gulp",
                adds="Tasks de assets clásicas",
                removes="Stack más contemporáneo (Webpack/Vite)",
                implication="Solo si tu equipo ya depende de Gulp.",
            ),
            Choice(
                value="Django Compressor",
                label="Django Compressor",
                adds="Compresión de estáticos en Django",
                removes="Bundler JS completo",
                implication="Bueno para CSS/JS ligeros sin Node build obligatorio.",
            ),
        ),
    ),
    Decision(
        key="ci_tool",
        title="CI",
        subtitle="¿Qué integración continua generamos?",
        why="La plantilla puede dejar workflows listos. **Github** encaja con repos en GitHub Actions.",
        default="Github",
        choices=(
            Choice(
                value="Github",
                label="Github Actions (recomendado)",
                adds="Workflow CI en `.github/`",
                removes="Nada si usas GitHub",
                implication="Lint/tests desde el primer push.",
            ),
            Choice(
                value="Gitlab",
                label="Gitlab CI",
                adds="Config GitLab CI",
                removes="GitHub Actions",
                implication="Elige esto solo si el remoto es GitLab.",
            ),
            Choice(
                value="None",
                label="None — sin CI en la plantilla",
                adds="Repo más limpio al inicio",
                removes="Pipeline generado",
                implication="Deberás añadir CI manualmente.",
            ),
        ),
    ),
    Decision(
        key="use_whitenoise",
        title="WhiteNoise",
        subtitle="¿Servir estáticos desde Django/app server?",
        why=(
            "**WhiteNoise** sirve archivos estáticos sin Nginx dedicado en muchos deploys simples. "
            "Con CDN/object storage a veces no hace falta."
        ),
        default="y",
        choices=(
            Choice(
                value="y",
                label="Sí — WhiteNoise (recomendado)",
                adds="Estáticos robustos en PaaS/simple hosting",
                removes="Nada habitual",
                implication="Buen default; puedes complementar con CDN luego.",
            ),
            Choice(
                value="n",
                label="No — sin WhiteNoise",
                adds="Menos middleware",
                removes="Serving de estáticos out-of-the-box",
                implication="Úsalo si un reverse proxy/CDN cubrirá `/static/`.",
            ),
        ),
    ),
    Decision(
        key="use_sentry",
        title="Sentry",
        subtitle="¿Incluir monitoreo de errores Sentry?",
        why="**Sentry** captura excepciones en producción. Requiere DSN/cuenta.",
        default="n",
        choices=(
            Choice(
                value="n",
                label="No — sin Sentry (recomendado al inicio)",
                adds="Menos secretos/config",
                removes="Error tracking listo",
                implication="Puedes añadirlo cuando tengas entorno prod.",
            ),
            Choice(
                value="y",
                label="Sí — preparar Sentry",
                adds="Hooks/config Sentry en la plantilla",
                removes="Onboarding más corto",
                implication="Necesitarás configurar el DSN en env vars.",
            ),
        ),
    ),
    Decision(
        key="cloud_provider",
        title="Cloud provider",
        subtitle="¿Proveedor cloud para media/storage?",
        why=(
            "La plantilla puede cablear backends de media para **AWS**, **GCP** o **Azure**. "
            "**None** evita credenciales cloud al inicio."
        ),
        default="None",
        choices=(
            Choice(
                value="None",
                label="None — sin cloud storage (recomendado)",
                adds="Menos secretos",
                removes="Media en cloud desde el día 1",
                implication="Media local/dev; añade cloud cuando deploys en serio.",
            ),
            Choice(
                value="AWS",
                label="AWS",
                adds="Integración típica S3/media",
                removes="Simplicidad local",
                implication="Necesitarás credenciales AWS.",
            ),
            Choice(
                value="GCP",
                label="GCP",
                adds="Integración Google Cloud",
                removes="Simplicidad local",
                implication="Necesitarás proyecto GCP y credenciales.",
            ),
            Choice(
                value="Azure",
                label="Azure",
                adds="Integración Azure",
                removes="Simplicidad local",
                implication="Necesitarás recursos Azure.",
            ),
        ),
    ),
    Decision(
        key="with_pgbouncer",
        title="PgBouncer",
        subtitle="¿Pool de conexiones PostgreSQL? (sigue siendo Postgres)",
        why=(
            "**PgBouncer** reduce RAM cuando hay muchos workers. "
            "El harness lo ofrece **opt-in**: plantillas Compose + settings con `USE_PGBOUNCER`. "
            "Solo tiene sentido con **Docker Compose**."
        ),
        default="n",
        requires=(("use_docker", "y"),),
        choices=(
            Choice(
                value="n",
                label="No — Postgres directo (recomendado al inicio)",
                adds="Topología simple: app → postgres",
                removes="Pooler extra",
                implication="Ideal en local y proyectos pequeños/medianos sin presión de conexiones.",
            ),
            Choice(
                value="y",
                label="Sí — activar PgBouncer",
                adds="Servicio pgbouncer, envs `USE_PGBOUNCER=True`, migrate bypass",
                removes="Conexión directa app→postgres en runtime",
                implication=(
                    "Úsalo en VPS con muchos workers. Las migraciones deben ir a Postgres directo."
                ),
            ),
        ),
    ),
)
