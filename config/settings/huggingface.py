import ssl
from .base import *  # noqa
from decouple import config

DEBUG = False

ALLOWED_HOSTS = ["*"]

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

# Allow HF Spaces to embed the app in an iframe
X_FRAME_OPTIONS = "ALLOWALL"

# Upstash Redis requires SSL cert config for rediss:// scheme
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": ssl.CERT_NONE},
        },
        "TIMEOUT": 300,
    }
}

# Serve React SPA index.html from staticfiles
TEMPLATES[0]["DIRS"] = [BASE_DIR / "staticfiles"]
