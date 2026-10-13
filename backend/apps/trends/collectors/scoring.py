"""Turn one day's CollectedSignal rows into that day's TrendSnapshot scores.

Idempotent: one DAY snapshot per product and local date, updated in place on
every run. Momentum compares with the previous *day*, not the previous run.

Example:
    refresh_snapshots_from_signals()
    # {"wrote": 2, "day": "2026-10-12"} — products with no signal keep their last snapshot
"""

from __future__ import annotations

from datetime import date, datetime

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product
from apps.trends.models import CollectedSignal, TrendSnapshot

MAX_SCORE = 100
DEFAULT_SCORE = 40
DEFAULT_EMERGING = 30


def _clip(value: float) -> int:
    return max(0, min(MAX_SCORE, int(round(value))))


def _demand_from_rank(rank: float) -> int:
    """Rank 1 (hottest) maps near 100; lower ranks still stay visible.

    Example:
        _demand_from_rank(1) == 100
        _demand_from_rank(10) == 55
    """
    return _clip(100 - (rank - 1) * 5)


def _supply_from_ads(count: float) -> int:
    """Each public ad id adds to supply, capped at 100.

    Example:
        _supply_from_ads(3) == 24
    """
    return _clip(count * 8)


def refresh_snapshots_from_signals(
    *,
    now: datetime | None = None,
    day: date | None = None,
) -> dict:
    """Upsert the DAY snapshot of every product that has a signal on `day`.

    Example:
        refresh_snapshots_from_signals()                     # today (Antananarivo)
        refresh_snapshots_from_signals(day=date(2026, 10, 1))  # recompute a past day
    """
    captured = now or timezone.now()
    target = day or timezone.localdate(captured)
    wrote = 0

    signals_by_product: dict[int, list[CollectedSignal]] = {}
    for signal in CollectedSignal.objects.filter(day=target, product__is_active=True):
        signals_by_product.setdefault(signal.product_id, []).append(signal)

    for product in Product.objects.filter(pk__in=signals_by_product.keys()):
        signals = signals_by_product[product.pk]
        with transaction.atomic():
            snapshots = TrendSnapshot.objects.select_for_update().filter(
                product=product,
                window=TrendSnapshot.Window.DAY,
            )
            previous = snapshots.filter(day__lt=target).order_by("-day").first()
            today = snapshots.filter(day=target).first()
            base = today or previous

            demand = base.demand_score if base else DEFAULT_SCORE
            supply = base.supply_score if base else DEFAULT_SCORE
            emerging = base.emerging_score if base else DEFAULT_EMERGING

            trend_ranks = [s.value for s in signals if s.metric == CollectedSignal.Metric.TREND_MATCH]
            ads_counts = [s.value for s in signals if s.metric == CollectedSignal.Metric.ADS_MATCH]

            if trend_ranks:
                demand = _demand_from_rank(min(trend_ranks))
                floor = previous.emerging_score if previous else 0
                emerging = _clip(max(floor, demand * 0.85))

            if ads_counts:
                supply = _supply_from_ads(sum(ads_counts))

            momentum = float(demand - previous.demand_score) if previous else 0.0
            seasonal = (
                _clip((previous.seasonal_baseline * 6 + demand) / 7) if previous else demand
            )

            TrendSnapshot.objects.update_or_create(
                product=product,
                window=TrendSnapshot.Window.DAY,
                day=target,
                defaults={
                    "captured_at": captured,
                    "demand_score": demand,
                    "supply_score": supply,
                    "momentum": momentum,
                    "seasonal_baseline": seasonal,
                    "emerging_score": emerging,
                },
            )
            wrote += 1

    return {"wrote": wrote, "day": target.isoformat()}
