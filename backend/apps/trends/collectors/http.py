"""Outbound HTTP for collectors. Always gates with assert_can_collect first.

v4 adds what a flaky 3G link to Meta / Google needs:

- split timeouts (connect vs read),
- retries with exponential backoff + jitter on timeouts, 429 and 5xx,
  honouring ``Retry-After``,
- an hourly request budget per source (shared through the cache, so
  worker restarts and parallel tasks see the same count),
- the legal gate re-checked against the database before *every* attempt:
  a consent revoked mid-run stops the very next request.

Example:
    with CollectorSession(source) as session:
        response = gated_request(source, "GET", url, params={"geo": "MG"}, session=session)
    session.stats  # {"requests": 1, "retries": 0}
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

import httpx
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.sources.models import Source
from apps.sources.policy import assert_can_collect

logger = logging.getLogger(__name__)

COLLECTOR_USER_AGENT = "Firona/4.0 (legal-collectors; geo=MG)"
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_AFTER_S = 60.0


class BudgetExceeded(Exception):
    """The source used its hourly request budget; no HTTP was sent."""


class RetriesExhausted(Exception):
    """Every attempt failed with a transient error (timeout, 429, 5xx)."""


def _setting(name: str, default):
    return getattr(settings, name, default)


def _budget_for(source: Source) -> int:
    budgets = _setting("COLLECT_BUDGET_PER_HOUR", {})
    return int(budgets.get(source.kind, budgets.get("default", 60)))


def consume_budget(source: Source) -> int:
    """Count one request against this source's hourly budget.

    Example:
        consume_budget(ads)  # 1, 2, … raises BudgetExceeded past the limit
    """
    hour = timezone.now().strftime("%Y%m%d%H")
    key = f"firona:budget:{source.pk}:{hour}"
    cache.add(key, 0, timeout=3700)
    try:
        used = cache.incr(key)
    except ValueError:  # key expired between add and incr
        cache.set(key, 1, timeout=3700)
        used = 1
    limit = _budget_for(source)
    if used > limit:
        raise BudgetExceeded(f"hourly budget of {limit} requests used for {source.name}")
    return used


def retry_after_seconds(header: str | None, *, now: float | None = None) -> float | None:
    """Parse ``Retry-After`` (delta-seconds or HTTP-date) into seconds, or None.

    Example:
        retry_after_seconds("7") == 7.0
        retry_after_seconds("Wed, 21 Oct 2026 07:28:00 GMT")  # seconds until then
    """
    if not header:
        return None
    value = header.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        moment = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if moment is None:
        return None
    return max(0.0, moment.timestamp() - (time.time() if now is None else now))


def backoff_delay(attempt: int) -> float:
    """Seconds to wait before retry `attempt` (1-based): exponential, full jitter.

    Example:
        backoff_delay(1)  # 0..1 s
        backoff_delay(3)  # 0..4 s
    """
    base = float(_setting("COLLECT_RETRY_BASE_S", 1.0))
    cap = float(_setting("COLLECT_RETRY_CAP_S", 20.0))
    return random.uniform(0, min(cap, base * 2 ** (attempt - 1)))


def _timeout() -> httpx.Timeout:
    read = float(_setting("COLLECT_HTTP_TIMEOUT", 20))
    return httpx.Timeout(read, connect=min(read, 6.0))


@dataclass
class CollectorSession:
    """One pooled HTTP client + counters for a collector run on one source."""

    source: Source
    stats: dict = field(default_factory=lambda: {"requests": 0, "retries": 0})
    _client: httpx.Client | None = None

    def __enter__(self) -> CollectorSession:
        self._client = httpx.Client(
            timeout=_timeout(),
            follow_redirects=True,
            headers={"User-Agent": COLLECTOR_USER_AGENT},
        )
        return self

    def __exit__(self, *_exc) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("CollectorSession must be used as a context manager")
        return self._client


def _refresh_gate(source: Source) -> None:
    """Reload consent/activation flags so a revoke in admin applies immediately."""
    if source.pk:
        source.refresh_from_db(fields=["is_active", "consent_granted", "consent_revoked_at", "kind"])
    assert_can_collect(source)


def gated_request(
    source: Source,
    method: str,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    session: CollectorSession | None = None,
    follow_redirects: bool = True,
) -> httpx.Response:
    """GET/POST only after the legal gate, with retries. Raises CollectionDenied before any socket.

    Returns the last response for non-retryable statuses (4xx except 429) so
    the collector can record the API's own error. Raises RetriesExhausted when
    every attempt hit a timeout / 429 / 5xx, or when the server asks to wait
    longer than 60 s. Pass ``follow_redirects=False`` when the URL carries a
    secret, so a captive portal cannot bounce it to another host.

    Example:
        response = gated_request(source, "GET", "https://example.test/rss")
        response.raise_for_status()
    """
    assert_can_collect(source)

    own_session = session is None
    if own_session:
        session = CollectorSession(source).__enter__()
    attempts = max(1, int(_setting("COLLECT_HTTP_ATTEMPTS", 3)))
    last_problem = ""
    try:
        for attempt in range(1, attempts + 1):
            # Re-read consent / activation before *every* request, not only retries.
            _refresh_gate(source)
            consume_budget(source)
            session.stats["requests"] += 1
            try:
                response = session.client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    follow_redirects=follow_redirects,
                )
            except httpx.TransportError as exc:
                last_problem = f"{type(exc).__name__}"
                wait = None
            else:
                if response.status_code not in RETRY_STATUSES:
                    return response
                last_problem = f"HTTP {response.status_code}"
                wait = retry_after_seconds(response.headers.get("Retry-After"))

            if wait is not None and wait > MAX_RETRY_AFTER_S:
                raise RetriesExhausted(f"{last_problem}: server asked to wait {wait:.0f}s")
            if attempt == attempts:
                break
            delay = wait if wait is not None else backoff_delay(attempt)
            session.stats["retries"] += 1
            logger.warning(
                "collector %s: %s on attempt %s/%s, retrying in %.1fs",
                source.name,
                last_problem,
                attempt,
                attempts,
                delay,
            )
            time.sleep(delay)
        raise RetriesExhausted(f"{last_problem} after {attempts} attempts")
    finally:
        if own_session:
            session.__exit__(None, None, None)
