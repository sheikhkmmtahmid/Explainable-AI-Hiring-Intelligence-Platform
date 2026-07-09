"""
Health check endpoint for load balancers, uptime monitors, and container
orchestration to poll. Actually checks the dependencies this app needs to
function (database, cache), not just "did Django start" -- a process that
started fine but lost its database connection should report unhealthy, not
a blind 200.
"""
import logging

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    checks = {}
    healthy = True

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except OperationalError as exc:
        checks["database"] = "unreachable"
        healthy = False
        logger.error("Health check: database unreachable: %s", exc)

    try:
        from django.core.cache import cache
        cache.set("health_check_probe", "1", timeout=5)
        checks["cache"] = "ok" if cache.get("health_check_probe") == "1" else "unreachable"
        if checks["cache"] != "ok":
            healthy = False
    except Exception as exc:
        checks["cache"] = "unreachable"
        healthy = False
        logger.error("Health check: cache unreachable: %s", exc)

    status_code = 200 if healthy else 503
    return JsonResponse({"status": "healthy" if healthy else "unhealthy", "checks": checks}, status=status_code)
