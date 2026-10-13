"""Celery tasks. Collectors always call assert_can_collect before HTTP.

v4: one collect at a time (cache lock), soft/hard time limits, automatic
retry when the database blips, a worker heartbeat for /api/v1/status/, and
a daily prune of the run log.

Example:
    from apps.trends.tasks import collect_legal_sources
    collect_legal_sources.delay()
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db import InterfaceError, OperationalError
from django.utils import timezone

from apps.sources.models import Source
from apps.sources.policy import CollectionDenied, assert_can_collect
from apps.trends.collectors import collect_legal_sources as run_collect_legal_sources
from apps.trends.collectors.google_trends import collect_google_trends as run_google_trends
from apps.trends.collectors.meta_ads import collect_meta_ads as run_meta_ads
from apps.trends.collectors.scoring import refresh_snapshots_from_signals
from apps.trends.models import CollectionRun

logger = logging.getLogger(__name__)

COLLECT_LOCK_KEY = "firona:lock:collect"
HEARTBEAT_KEY = "firona:heartbeat:worker"

SOFT_LIMIT = int(getattr(settings, "COLLECT_SOFT_TIME_LIMIT", 900))
COLLECT_TASK_OPTIONS = {
    "soft_time_limit": SOFT_LIMIT,
    "time_limit": SOFT_LIMIT + 120,
    # Database / connection blips: retry the whole task later, with jitter.
    "autoretry_for": (OperationalError, InterfaceError),
    "retry_backoff": 30,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "max_retries": 3,
}


@contextmanager
def single_flight(key: str, ttl: int):
    """Yield True when this worker owns `key`, False if another run holds it.

    Example:
        with single_flight("firona:lock:collect", 1200) as owned:
            if owned:
                collect()
    """
    token = uuid.uuid4().hex
    owned = cache.add(key, token, timeout=ttl)
    try:
        yield owned
    finally:
        if owned and cache.get(key) == token:
            cache.delete(key)


def run_locked(run: Callable[[], dict]) -> dict:
    """Run a collector unless another collect holds the lock (beat, manual, retry).

    Example:
        run_locked(collect_legal_sources)  # {"skipped": "..."} when busy
    """
    with single_flight(COLLECT_LOCK_KEY, SOFT_LIMIT + 300) as owned:
        if not owned:
            logger.info("collect skipped: another collect is still running")
            return {"skipped": "another collect is still running"}
        return run()


@shared_task
def ping_stack() -> str:
    """Lightweight heartbeat so the worker service can be verified."""
    return "ok"


@shared_task(ignore_result=True)
def heartbeat() -> str:
    """Beat → broker → worker loop is alive; read by /api/v1/status/.

    Example:
        heartbeat.delay()
    """
    stamp = timezone.now().isoformat()
    cache.set(HEARTBEAT_KEY, stamp, timeout=None)
    return stamp


@shared_task
def audit_sources() -> dict:
    """Classify every Source without calling the internet.

    Example:
        result = audit_sources()
        # {"collectable": ["Google Trends MG"], "blocked": [{"name": "...", "reason": "..."}]}
    """
    allowed: list[str] = []
    blocked: list[dict] = []
    for source in Source.objects.all():
        try:
            assert_can_collect(source)
        except CollectionDenied as exc:
            blocked.append({"name": source.name, "kind": source.kind, "reason": str(exc)})
        else:
            allowed.append(source.name)
    return {"collectable": allowed, "blocked": blocked}


@shared_task(**COLLECT_TASK_OPTIONS)
def collect_google_trends() -> dict:
    """Celery entry for the MG Trends RSS collector.

    Example:
        collect_google_trends.delay()
    """
    return run_locked(run_google_trends)


@shared_task(**COLLECT_TASK_OPTIONS)
def collect_meta_ads() -> dict:
    """Celery entry for the Ads Library collector.

    Example:
        collect_meta_ads.delay()
    """
    return run_locked(run_meta_ads)


@shared_task(**COLLECT_TASK_OPTIONS)
def collect_legal_sources() -> dict:
    """Fetch Ads Library + Trends MG, then write today's TrendSnapshot for matches.

    Example:
        collect_legal_sources.delay()
    """
    return run_locked(run_collect_legal_sources)


@shared_task(autoretry_for=(OperationalError, InterfaceError), retry_backoff=30, max_retries=3)
def refresh_radar_snapshots() -> dict:
    """Recompute today's scores from signals already stored (no HTTP).

    Example:
        refresh_radar_snapshots.delay()
    """
    return refresh_snapshots_from_signals()


@shared_task
def prune_collection_runs() -> dict:
    """Close runs orphaned by a killed worker; drop runs past the retention window.

    Example:
        prune_collection_runs()  # {"orphaned": 0, "deleted": 12}
    """
    now = timezone.now()
    orphaned = CollectionRun.objects.filter(
        status=CollectionRun.Status.RUNNING,
        started_at__lt=now - timedelta(seconds=SOFT_LIMIT + 3600),
    ).update(
        status=CollectionRun.Status.ERROR,
        finished_at=now,
        detail="worker stopped before the run finished",
    )
    days = int(getattr(settings, "COLLECT_RUN_RETENTION_DAYS", 90))
    deleted, _ = CollectionRun.objects.filter(started_at__lt=now - timedelta(days=days)).delete()
    return {"orphaned": orphaned, "deleted": deleted}
