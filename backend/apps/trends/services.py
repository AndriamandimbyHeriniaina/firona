"""Radar assembly: pick the right snapshot scores for now / past / future.

Example:
    from apps.trends.services import build_radar
    payload = build_radar(horizon="now")
"""

from __future__ import annotations

from django.db.models import OuterRef, Subquery

from apps.catalog.models import Product
from apps.trends.models import TrendSnapshot

VALID_HORIZONS = ("now", "past", "future")


def _label(momentum: float, emerging: int) -> str:
    if emerging >= 70 and momentum > 0:
        return "emerging"
    if momentum >= 8:
        return "rising"
    if momentum <= -8:
        return "falling"
    return "stable"


def build_radar(*, horizon: str) -> list[dict]:
    """Return one radar row per active product for the requested horizon."""
    if horizon not in VALID_HORIZONS:
        horizon = "now"

    latest = TrendSnapshot.objects.filter(
        product=OuterRef("pk"),
        window=TrendSnapshot.Window.DAY,
    ).order_by("-captured_at")

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

        if horizon == "past":
            score = int(product.latest_seasonal)
        elif horizon == "future":
            score = int(product.latest_emerging)
        else:
            score = int(product.latest_demand)

        momentum = float(product.latest_momentum or 0)
        emerging = int(product.latest_emerging or 0)
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
                },
                "horizon": horizon,
                "score": score,
                "demand_score": int(product.latest_demand),
                "supply_score": int(product.latest_supply or 0),
                "momentum": momentum,
                "emerging_score": emerging,
                "label": _label(momentum, emerging),
                "captured_at": product.latest_at,
            }
        )

    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows
