"""Google Trends collector: public RSS, geo=MG only. No HTML scrape.

Idempotent per local day: re-running keeps one signal per product and
source, with the best rank seen that day.

Example:
    result = collect_google_trends()
    # {"ok": True, "signals": 2, "unmatched": 10} or {"ok": False, "error": "..."}
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime

from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product
from apps.sources.models import Source
from apps.sources.policy import TRENDS_GEO, CollectionDenied, assert_can_collect
from apps.sources.redact import redact
from apps.trends.collectors.http import CollectorSession, gated_request
from apps.trends.collectors.matching import match_title_to_product
from apps.trends.collectors.runs import RunLog
from apps.trends.models import CollectedSignal, CollectionRun

logger = logging.getLogger(__name__)

TRENDS_RSS_URL = "https://trends.google.com/trending/rss"
HT_NS = "https://trends.google.com/trending/rss"
MAX_TITLES = 10


def parse_approx_traffic(label: str) -> float:
    """Turn Google's '1,000+' label into a number for storage.

    Example:
        parse_approx_traffic("1,000+") == 1000.0
    """
    digits = "".join(ch for ch in label if ch.isdigit())
    return float(digits) if digits else 0.0


def parse_trends_rss(xml_text: str) -> list[dict]:
    """Extract public search titles from a Daily Search Trends RSS document.

    Example:
        rows = parse_trends_rss(xml)
        rows[0]["title"]  # "riz"
    """
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    for index, item in enumerate(root.findall("./channel/item"), start=1):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        traffic_el = item.find(f"{{{HT_NS}}}approx_traffic")
        traffic_label = (traffic_el.text or "").strip() if traffic_el is not None else ""
        items.append(
            {
                "title": title,
                "rank": index,
                "approx_traffic": traffic_label,
                "traffic_value": parse_approx_traffic(traffic_label),
            }
        )
    return items


def _assert_trends_geo(source: Source) -> str:
    geo = (source.external_id or TRENDS_GEO).strip().upper() or TRENDS_GEO
    if geo != TRENDS_GEO:
        raise CollectionDenied(f"google_trends geo must be {TRENDS_GEO}, got {geo}")
    return geo


@transaction.atomic
def upsert_trend_signal(
    *,
    source: Source,
    product: Product,
    term: str,
    row: dict,
    captured: datetime,
    day: date,
    geo: str,
) -> CollectedSignal:
    """Keep the best (lowest) rank of the day and up to 10 matching titles.

    Example:
        upsert_trend_signal(source=s, product=p, term="findy", row={"title": "findy", "rank": 3, ...}, ...)
    """
    rank = float(row["rank"])
    # get_or_create survives a concurrent insert (unique key) by re-reading the row.
    signal, created = CollectedSignal.objects.get_or_create(
        source=source,
        product=product,
        metric=CollectedSignal.Metric.TREND_MATCH,
        day=day,
        defaults={
            "captured_at": captured,
            "query": term,
            "value": rank,
            "payload": {
                "titles": [row["title"]],
                "rank": row["rank"],
                "approx_traffic": row["approx_traffic"],
                "geo": geo,
            },
        },
    )
    if created:
        return signal
    signal = CollectedSignal.objects.select_for_update().get(pk=signal.pk)
    payload = dict(signal.payload or {})
    titles = list(payload.get("titles") or [])
    if row["title"] not in titles:
        titles.append(row["title"])
    payload["titles"] = titles[:MAX_TITLES]
    payload["geo"] = geo
    if rank < signal.value:
        signal.value = rank
        signal.query = term
        payload["rank"] = row["rank"]
        payload["approx_traffic"] = row["approx_traffic"]
    signal.payload = payload
    signal.captured_at = captured
    signal.save(update_fields=["value", "query", "payload", "captured_at"])
    return signal


def collect_google_trends(*, now: datetime | None = None) -> dict:
    """Fetch MG daily trends and store matches against existing Product aliases.

    Example:
        collect_google_trends()
        # Unmatched titles are counted, never inserted as new articles.
    """
    captured = now or timezone.now()
    day = timezone.localdate(captured)
    sources = list(Source.objects.filter(kind=Source.Kind.GOOGLE_TRENDS))
    if not sources:
        return {"ok": False, "error": "no google_trends source"}

    products = list(Product.objects.filter(is_active=True))
    totals = {"ok": True, "signals": 0, "unmatched": 0, "skipped": 0, "sources": []}

    for source in sources:
        log = RunLog(source, "google_trends")
        try:
            assert_can_collect(source)
            geo = _assert_trends_geo(source)
        except CollectionDenied as exc:
            logger.info("skip trends source %s: %s", source.name, exc)
            log.close(CollectionRun.Status.SKIPPED, detail=str(exc))
            totals["skipped"] += 1
            totals["sources"].append({"name": source.name, "skipped": str(exc)})
            continue

        with CollectorSession(source) as session:
            try:
                response = gated_request(
                    source,
                    "GET",
                    TRENDS_RSS_URL,
                    params={"geo": geo},
                    session=session,
                )
                if response.status_code >= 400:
                    message = (
                        f"Google Trends RSS HTTP {response.status_code} for geo={geo}. "
                        "Madagascar has no public daily RSS on some dates; "
                        "snapshots stay unchanged."
                    )
                    source.mark_error(message)
                    log.close(CollectionRun.Status.ERROR, detail=message, stats=session.stats)
                    totals["ok"] = False
                    totals["sources"].append({"name": source.name, "error": message})
                    continue

                rows = parse_trends_rss(response.text)
                linked_ids = set(
                    Product.objects.filter(is_active=True, sources=source).values_list("pk", flat=True)
                )
                linked = [item for item in products if item.pk in linked_ids] or products

                unmatched = 0
                touched: set[int] = set()
                for row in rows:
                    matched = match_title_to_product(row["title"], linked)
                    if not matched:
                        unmatched += 1
                        continue
                    product, term = matched
                    upsert_trend_signal(
                        source=source,
                        product=product,
                        term=term,
                        row=row,
                        captured=captured,
                        day=day,
                        geo=geo,
                    )
                    touched.add(product.pk)

                source.mark_success()
                log.close(CollectionRun.Status.OK, signals=len(touched), stats=session.stats)
                totals["signals"] += len(touched)
                totals["unmatched"] += unmatched
                totals["sources"].append(
                    {"name": source.name, "signals": len(touched), "unmatched": unmatched}
                )
            except SoftTimeLimitExceeded:
                log.close(CollectionRun.Status.ERROR, detail="soft time limit reached", stats=session.stats)
                source.mark_error("soft time limit reached")
                raise
            except CollectionDenied as exc:
                # Consent revoked / source disabled between two attempts: stop quietly.
                log.close(CollectionRun.Status.SKIPPED, detail=str(exc), stats=session.stats)
                totals["skipped"] += 1
                totals["sources"].append({"name": source.name, "skipped": str(exc)})
            except Exception as exc:  # noqa: BLE001 - collector must mark_error, not crash beat
                message = redact(f"{type(exc).__name__}: {exc}")
                # No traceback: exception text may echo a URL (proxy / portal pages).
                logger.error("google trends collect failed for %s: %s", source.name, message)
                source.mark_error(message)
                log.close(CollectionRun.Status.ERROR, detail=message, stats=session.stats)
                totals["ok"] = False
                totals["sources"].append({"name": source.name, "error": message})

    return totals
