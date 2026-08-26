"""Celery tasks. v2: audit only. v3: HTTP collectors behind assert_can_collect.

Example:
    from apps.trends.tasks import audit_sources
    audit_sources.delay()
"""

from celery import shared_task

from apps.sources.models import Source
from apps.sources.policy import CollectionDenied, assert_can_collect


@shared_task
def ping_stack() -> str:
    """Lightweight heartbeat so the worker service can be verified."""
    return "ok"


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
