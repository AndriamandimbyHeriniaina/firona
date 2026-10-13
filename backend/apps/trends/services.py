"""Radar assembly: pick the right snapshot scores for now / past / future.

Example:
    from apps.trends.services import build_radar, product_radar
    payload = build_radar(horizon="now")
    scores = product_radar(phone)  # {"now": {...}, "past": {...}, "future": {...}}
"""

from __future__ import annotations

from django.db.models import OuterRef, Subquery

from apps.catalog.models import Product
from apps.trends.models import TrendSnapshot

VALID_HORIZONS = ("now", "past", "future")

# Latest day first; captured_at breaks ties inside a day.
LATEST_FIRST = ("-day", "-captured_at")


def trend_label(momentum: float, emerging: int) -> str:
    """Card label from day-over-day momentum and the emerging score.

    Example:
        trend_label(12.0, 40) == "rising"
        trend_label(3.0, 80) == "emerging"
    """
    if emerging >= 70 and momentum > 0:
        return "emerging"
    if momentum >= 8:
        return "rising"
    if momentum <= -8:
        return "falling"
    return "stable"


def horizon_scores(
    horizon: str,
    *,
    demand: int,
    supply: int,
    momentum: float,
    seasonal: int,
    emerging: int,
    captured_at,
) -> dict:
    """Score block for one horizon from one snapshot's values."""
    if horizon == "past":
        score = seasonal
    elif horizon == "future":
        score = emerging
    else:
        score = demand
    return {
        "score": int(score),
        "demand_score": int(demand),
        "supply_score": int(supply),
        "momentum": float(momentum),
        "emerging_score": int(emerging),
        "label": trend_label(float(momentum), int(emerging)),
        "captured_at": captured_at,
    }


def build_radar(*, horizon: str) -> list[dict]:
    """Return one radar row per active product for the requested horizon."""
    if horizon not in VALID_HORIZONS:
        horizon = "now"

    latest = TrendSnapshot.objects.filter(
        product=OuterRef("pk"),
        window=TrendSnapshot.Window.DAY,
    ).order_by(*LATEST_FIRST)

    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .annotate(
            latest_demand=Subquery(latest.values("demand_score")[:1]),
            latest_supply=Subquery(latest.values("supply_score")[:1]),
            latest_momentum=Subquery(latest.values("momentum")[:1]),
            latest_seasonal=Subquery(latest.values("seasonal_baseline")[:1]),
            latest_emerging=Subquery(latest.values("emerging_score")[:1]),
            latest_at=Subquery(latest.values("captured_at")[:1]),
        )
    )

    rows: list[dict] = []
    for product in products:
        if product.latest_demand is None:
            continue
        rows.append(
            {
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "category": {
                        "id": product.category_id,
                        "name": product.category.name,
                        "slug": product.category.slug,
                    },
                    "aliases": product.aliases,
                    "description": product.description,
                    "image_url": product.image_url,
                    "gallery": product.gallery,
                    "where_to_find": product.where_to_find,
                },
                "horizon": horizon,
                **horizon_scores(
                    horizon,
                    demand=product.latest_demand,
                    supply=product.latest_supply or 0,
                    momentum=product.latest_momentum or 0,
                    seasonal=product.latest_seasonal or 0,
                    emerging=product.latest_emerging or 0,
                    captured_at=product.latest_at,
                ),
            }
        )

    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows


def product_radar(product: Product) -> dict[str, dict]:
    """All three horizons for one product from its latest DAY snapshot (one query).

    Example:
        product_radar(phone)["future"]["score"]  # emerging score
    """
    snap = (
        TrendSnapshot.objects.filter(product=product, window=TrendSnapshot.Window.DAY)
        .order_by(*LATEST_FIRST)
        .first()
    )
    if snap is None:
        return {}
    return {
        horizon: horizon_scores(
            horizon,
            demand=snap.demand_score,
            supply=snap.supply_score,
            momentum=snap.momentum,
            seasonal=snap.seasonal_baseline,
            emerging=snap.emerging_score,
            captured_at=snap.captured_at,
        )
        for horizon in VALID_HORIZONS
    }
