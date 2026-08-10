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
    default="UCCtONENksIXsVkqfm0znbrZ5FtfI9UhAgXRDnEYB7OcGCAMzhhixHUP7sityMx6",
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


# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]

# Your stuff...
# ------------------------------------------------------------------------------

# >>> django-ai-harness
# Extra DX from django-ai-harness (safe for local only)
INSTALLED_APPS += ["django_browser_reload", "django_linear_migrations"]
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]

# django-read-only: protect against accidental writes in shells when enabled
# Toggle with: import django_read_only; django_read_only.enable()
INSTALLED_APPS += ["django_read_only"]

# django-version-checks: keep environments aligned
INSTALLED_APPS += ["django_version_checks"]
VERSION_CHECKS = {
    "python": "~=3.14.0",
}

# Prefer IPython when available (django-extensions shell_plus)
SHELL_PLUS = "ipython"
# <<< django-ai-harness

# >>> django-ai-harness:pgbouncer
# Opt-in PgBouncer (transaction pooling). Keep ENGINE=postgresql.
# When USE_PGBOUNCER=True, point POSTGRES_HOST/PORT at the pooler and migrate via direct Postgres.
if env.bool("USE_PGBOUNCER", default=False):
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
# <<< django-ai-harness:pgbouncer
