"""Celery tasks for future collectors (Ads Library, partner pages, Trends).

Example:
    from apps.trends.tasks import ping_stack
    ping_stack.delay()
"""

from celery import shared_task


@shared_task
def ping_stack() -> str:
    """Lightweight heartbeat so the worker service can be verified."""
    return "ok"
