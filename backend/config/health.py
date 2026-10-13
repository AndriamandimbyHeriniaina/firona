"""Health endpoints.

- ``/api/health/``        liveness for Docker (no I/O, always cheap)
- ``/api/health/ready/``  readiness: database + cache answer (503 otherwise)
- ``/api/v1/status/``     service state for humans and monitors: worker
  heartbeat, queue backlog, per-source collect health, data freshness

Example:
    GET /api/health/        -> {"status": "ok"}
    GET /api/health/ready/  -> {"status": "ok", "checks": {"database": "ok", "cache": "ok"}}
    GET /api/v1/status/     -> {"status": "degraded", "checks": {...}, "sources": [...]}
"""

from __future__ import annotations

import logging
from datetime import datetime

import redis
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Max
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

HEARTBEAT_KEY = "firona:heartbeat:worker"
CELERY_QUEUE = "celery"


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


def _check_database() -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "ok"
    except Exception:  # noqa: BLE001 - report, do not raise from a probe
        logger.exception("readiness: database check failed")
        return "down"


def _check_cache() -> str:
    try:
        cache.set("firona:probe", "1", timeout=10)
        return "ok" if cache.get("firona:probe") == "1" else "down"
    except Exception:  # noqa: BLE001
        logger.exception("readiness: cache check failed")
        return "down"


def _queue_backlog() -> int | None:
    """Messages waiting in the default Celery queue (None if Redis is unreachable)."""
    try:
        client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        return int(client.llen(CELERY_QUEUE))
    except Exception:  # noqa: BLE001
        return None


def _age_seconds(moment: datetime | None, now: datetime) -> int | None:
    return None if moment is None else max(0, int((now - moment).total_seconds()))


@require_GET
@never_cache
def ready(_request):
    checks = {"database": _check_database(), "cache": _check_cache()}
    ok = all(value == "ok" for value in checks.values())
    return JsonResponse({"status": "ok" if ok else "down", "checks": checks}, status=200 if ok else 503)


@require_GET
@never_cache
def status(_request):
    """Overall state: ok, degraded (stale data, worker silent, source failing) or down."""
    from apps.sources.models import Source
    from apps.sources.policy import COLLECTABLE_KINDS
    from apps.trends.models import TrendSnapshot

    now = timezone.now()
    database = _check_database()
    cache_state = _check_cache()

    raw_beat = cache.get(HEARTBEAT_KEY) if cache_state == "ok" else None
    beat_at = parse_datetime(raw_beat) if isinstance(raw_beat, str) else None
    beat_age = _age_seconds(beat_at, now)
    worker_ok = beat_age is not None and beat_age <= settings.STATUS_HEARTBEAT_MAX_AGE_S

    backlog = _queue_backlog()
    queue_ok = backlog is not None and backlog <= settings.STATUS_QUEUE_WARN

    sources: list[dict] = []
    latest_at = None
    if database == "ok":
        for source in Source.objects.filter(kind__in=COLLECTABLE_KINDS).order_by("name"):
            sources.append(
                {
                    "name": source.name,
                    "kind": source.kind,
                    "health": source.health,
                    "last_success_at": source.last_success_at,
                    "last_error_at": source.last_error_at,
                    "consecutive_failures": source.consecutive_failures,
                }
            )
        latest_at = TrendSnapshot.objects.aggregate(latest=Max("captured_at"))["latest"]

    data_age = _age_seconds(latest_at, now)
    data_stale = data_age is None or data_age > settings.STATUS_STALE_HOURS * 3600
    failing = [item["name"] for item in sources if item["health"] == "error"]

    if database != "ok":
        overall = "down"
    elif cache_state != "ok" or not worker_ok or not queue_ok or data_stale or failing:
        overall = "degraded"
    else:
        overall = "ok"

    payload = {
        "status": overall,
        "time": now,
        "checks": {
            "database": database,
            "cache": cache_state,
            "worker": {
                "ok": worker_ok,
                "last_heartbeat": beat_at,
                "age_seconds": beat_age,
            },
            "queue": {"ok": queue_ok, "pending": backlog},
            "data": {
                "ok": not data_stale,
                "latest_snapshot_at": latest_at,
                "age_hours": None if data_age is None else round(data_age / 3600, 1),
                "stale_after_hours": settings.STATUS_STALE_HOURS,
            },
        },
        "sources": sources,
        "failing_sources": failing,
    }
    return JsonResponse(payload, status=503 if overall == "down" else 200)

