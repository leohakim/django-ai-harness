from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-ai-harness-golden-example-secret-key-not-for-real-use-0001",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]  # noqa: S104

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Disable profiling panel due to an issue with Python 3.12+:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join([*ip.split(".")[:-1], "1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]

# Your stuff...
# ------------------------------------------------------------------------------

# >>> django-ai-harness:local
# Local-only developer experience. Anything here is intentionally absent from
# production and from config.settings.test.
INSTALLED_APPS += ["django_browser_reload", "django_read_only", "django_rich"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# django-read-only guards against accidental writes in an interactive shell.
# It stays inert until you opt in:
#     import django_read_only; django_read_only.enable()
# Prefer IPython for `shell_plus`.
SHELL_PLUS = "ipython"

# Rich console logging. We deliberately patch the handler that base.py already defines
# instead of replacing LOGGING wholesale, so upstream loggers and formatters survive.
LOGGING["formatters"]["rich"] = {"datefmt": "[%X]"}
LOGGING["handlers"]["console"] = {
    "level": "DEBUG",
    "class": "rich.logging.RichHandler",
    "formatter": "rich",
    "rich_tracebacks": True,
}
# <<< django-ai-harness:local

# >>> django-ai-harness:pgbouncer
# Opt-in transaction pooling. Inert unless USE_PGBOUNCER is set; the engine stays
# PostgreSQL either way. See knowledge/dx-practices/postgres-pooling.md.
if env.bool("USE_PGBOUNCER", default=False):
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
    # PgBouncer in transaction mode cannot hold server-side cursors across statements.
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

    # A direct, unpooled alias for DDL. Run migrations with:
    #     python manage.py migrate --database=direct
    # TEST["MIRROR"] keeps the test runner from creating a second test database.
    DATABASES["direct"] = {
        **DATABASES["default"],
        "HOST": env("POSTGRES_HOST_DIRECT", default="postgres"),
        "PORT": env.int("POSTGRES_PORT_DIRECT", default=5432),
        "CONN_MAX_AGE": 0,
        "DISABLE_SERVER_SIDE_CURSORS": False,
        "TEST": {"MIRROR": "default"},
    }
# <<< django-ai-harness:pgbouncer
