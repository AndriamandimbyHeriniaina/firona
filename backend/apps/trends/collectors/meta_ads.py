"""Meta Ads Library collector: official Graph ads_archive, country MG only.

Idempotent per local day: the signal value is the number of distinct public
ad ids seen for the product that day, however many runs happened.

Example:
    result = collect_meta_ads()
    # {"ok": True, "signals": 3} or {"ok": False, "error": "META_ADS_ACCESS_TOKEN is empty"}
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from django.conf import settings
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product
from apps.sources.models import Source
from apps.sources.policy import ADS_REACHED_COUNTRY, CollectionDenied, assert_can_collect
from apps.sources.redact import redact
from apps.trends.collectors.http import CollectorSession, gated_request
from apps.trends.collectors.matching import product_terms
from apps.trends.collectors.runs import RunLog
from apps.trends.models import CollectedSignal, CollectionRun

logger = logging.getLogger(__name__)

# Non-EU countries only return social-issue / political ads in Ads Library.
ADS_TYPE = "POLITICAL_AND_ISSUE_ADS"
MAX_TERMS_PER_PRODUCT = 2
ADS_LIMIT = 25
MAX_STORED_IDS = 100


def _ads_archive_url() -> str:
    version = getattr(settings, "META_GRAPH_API_VERSION", "v21.0")
    return f"https://graph.facebook.com/{version}/ads_archive"


@transaction.atomic
def upsert_ads_signal(
    *,
    source: Source,
    product: Product,
    ad_ids: list[str],
    captured: datetime,
    day: date,
) -> CollectedSignal:
    """Union today's public ad ids for this product; value = distinct count.

    Example:
        upsert_ads_signal(source=ads, product=phone, ad_ids=["1", "2"], captured=now, day=today)
    """
    # get_or_create survives a concurrent insert (unique key) by re-reading the row.
    signal, created = CollectedSignal.objects.get_or_create(
        source=source,
        product=product,
        metric=CollectedSignal.Metric.ADS_MATCH,
        day=day,
        defaults={
            "captured_at": captured,
            "query": product.slug,
            "value": float(len(ad_ids)),
            "payload": {
                "ad_ids": ad_ids[:MAX_STORED_IDS],
                "count": len(ad_ids),
                "country": ADS_REACHED_COUNTRY,
            },
        },
    )
    if created:
        return signal
    signal = CollectedSignal.objects.select_for_update().get(pk=signal.pk)
    known = list((signal.payload or {}).get("ad_ids") or [])
    merged = known + [ad_id for ad_id in ad_ids if ad_id not in known]
    signal.payload = {
        "ad_ids": merged[:MAX_STORED_IDS],
        "count": len(merged),
        "country": ADS_REACHED_COUNTRY,
    }
    signal.value = float(len(merged))
    signal.captured_at = captured
    signal.save(update_fields=["value", "payload", "captured_at"])
    return signal


def collect_meta_ads(*, now: datetime | None = None) -> dict:
    """Search Ads Library per curated product; store public ad ids only.

    Example:
        collect_meta_ads()  # no creative bodies, phones, or comments
    """
    captured = now or timezone.now()
    day = timezone.localdate(captured)
    token = (getattr(settings, "META_ADS_ACCESS_TOKEN", "") or "").strip()
    sources = list(Source.objects.filter(kind=Source.Kind.META_ADS))
    if not sources:
        return {"ok": False, "error": "no meta_ads source"}

    totals = {"ok": True, "signals": 0, "skipped": 0, "sources": []}

    for source in sources:
        log = RunLog(source, "meta_ads")
        try:
            assert_can_collect(source)
        except CollectionDenied as exc:
            logger.info("skip ads source %s: %s", source.name, exc)
            log.close(CollectionRun.Status.SKIPPED, detail=str(exc))
            totals["skipped"] += 1
            totals["sources"].append({"name": source.name, "skipped": str(exc)})
            continue

        if not token:
            message = "META_ADS_ACCESS_TOKEN is empty; Ads Library was not called"
            source.mark_error(message)
            log.close(CollectionRun.Status.SKIPPED, detail=message)
            totals["ok"] = False
            totals["sources"].append({"name": source.name, "error": message})
            continue

        products = list(Product.objects.filter(is_active=True, sources=source))
        if not products:
            products = list(Product.objects.filter(is_active=True))

        stored = 0
        with CollectorSession(source) as session:
            try:
                for product in products:
                    terms = product_terms(product)[:MAX_TERMS_PER_PRODUCT]
                    ad_ids: list[str] = []
                    for term in terms:
                        response = gated_request(
                            source,
                            "GET",
                            _ads_archive_url(),
                            params={
                                "access_token": token,
                                "search_terms": term,
                                "ad_reached_countries": f"['{ADS_REACHED_COUNTRY}']",
                                "ad_type": ADS_TYPE,
                                "ad_active_status": "ALL",
                                "fields": "id",
                                "limit": ADS_LIMIT,
                            },
                            session=session,
                            # The token is in the query string: never follow it elsewhere.
                            follow_redirects=False,
                        )
                        if response.status_code >= 300:
                            raise RuntimeError(
                                f"Ads Library HTTP {response.status_code}: {response.text[:300]}"
                            )
                        payload = response.json()
                        if payload.get("error"):
                            raise RuntimeError(str(payload["error"]))
                        for row in payload.get("data") or []:
                            ad_id = str(row.get("id") or "")
                            if ad_id and ad_id not in ad_ids:
                                ad_ids.append(ad_id)

                    if not ad_ids:
                        continue
                    upsert_ads_signal(
                        source=source,
                        product=product,
                        ad_ids=ad_ids,
                        captured=captured,
                        day=day,
                    )
                    stored += 1

                source.mark_success()
                log.close(CollectionRun.Status.OK, signals=stored, stats=session.stats)
                totals["signals"] += stored
                totals["sources"].append({"name": source.name, "signals": stored})
            except SoftTimeLimitExceeded:
                log.close(CollectionRun.Status.ERROR, detail="soft time limit reached", signals=stored, stats=session.stats)
                source.mark_error("soft time limit reached")
                raise
            except CollectionDenied as exc:
                log.close(CollectionRun.Status.SKIPPED, detail=str(exc), signals=stored, stats=session.stats)
                totals["skipped"] += 1
                totals["sources"].append({"name": source.name, "skipped": str(exc)})
            except Exception as exc:  # noqa: BLE001 - mark_error, keep beat alive
                message = redact(f"{type(exc).__name__}: {exc}")
                # No traceback: exception text may echo the token-bearing URL.
                logger.error("meta ads collect failed for %s: %s", source.name, message)
                source.mark_error(message)
                log.close(CollectionRun.Status.ERROR, detail=message, signals=stored, stats=session.stats)
                totals["ok"] = False
                totals["sources"].append({"name": source.name, "error": message})

    return totals
