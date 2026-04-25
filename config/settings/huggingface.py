from .base import *  # noqa
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv())

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE[1:]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# React build served as static files
STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "frontend" / "dist"]

# HF Spaces sits behind a proxy that handles HTTPS — don't redirect
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Media: local storage is fine for a demo (ephemeral container)
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# CORS — allow HF space domain
CORS_ALLOW_ALL_ORIGINS = True
