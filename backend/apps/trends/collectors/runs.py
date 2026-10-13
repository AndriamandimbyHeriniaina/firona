"""CollectionRun bookkeeping shared by every collector.

Example:
    log = RunLog(source, "google_trends")
    ...
    log.close(CollectionRun.Status.OK, signals=3, stats=session.stats)
"""

from __future__ import annotations

import time

from django.utils import timezone

from apps.sources.models import Source
from apps.sources.redact import redact
from apps.trends.models import CollectionRun


class RunLog:
    """Opens a `running` row now, closes it with counts, duration and a redacted detail."""

    def __init__(self, source: Source, collector: str):
        self._t0 = time.monotonic()
        self.run = CollectionRun.objects.create(
            source=source,
            collector=collector,
            started_at=timezone.now(),
        )

    def close(
        self,
        status: str,
        *,
        signals: int = 0,
        detail: str = "",
        stats: dict | None = None,
    ) -> CollectionRun:
        stats = stats or {}
        run = self.run
        run.status = status
        run.finished_at = timezone.now()
        run.duration_ms = int((time.monotonic() - self._t0) * 1000)
        run.signals = signals
        run.requests = int(stats.get("requests", 0))
        run.retries = int(stats.get("retries", 0))
        run.detail = redact(detail)[:2000]
        run.save(
            update_fields=[
                "status",
                "finished_at",
                "duration_ms",
                "signals",
                "requests",
                "retries",
                "detail",
            ]
        )
        return run
