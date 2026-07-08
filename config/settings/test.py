from .base import *  # noqa

DEBUG = False

# django_celery_beat ships a long, real-world migration history that
# combines "ADD COLUMN" + "ADD FOREIGN KEY" into a single ALTER TABLE for
# two fields (PeriodicTask.solar, PeriodicTask.clocked) -- this specific
# TiDB instance silently fails that combined form (reproduced multiple
# times; see project memory). That's fine to work around by hand on the
# one long-lived dev database, but a disposable test database needs to be
# buildable from scratch every time without manual intervention. Point
# this app at a small local migration set (apps/celery_beat_migrations)
# that creates the exact same final schema, generated from Django's own
# model introspection, with db_constraint=False on those two fields so the
# problematic combined DDL is never emitted in the first place.
MIGRATION_MODULES = {
    "django_celery_beat": "apps.celery_beat_migrations",
    # Same story, different symptom: token_blacklist's historical migrations
    # try to add a UNIQUE column via ALTER TABLE, which this TiDB rejects
    # outright ("unsupported add column ... constraint UNIQUE KEY").
    # Consolidated into one CreateModel-based migration for the same reason.
    "token_blacklist": "apps.token_blacklist_migrations",
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
