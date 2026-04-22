from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Allow all origins in dev
CORS_ALLOW_ALL_ORIGINS = True

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# More verbose logging in dev
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
LOGGING["loggers"]["ml"]["level"] = "DEBUG"
