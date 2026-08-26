"""Assemble the article detail payload (catalog + radar + history).

Example:
    from apps.catalog.services import build_product_detail
    payload = build_product_detail("telephone")
"""

from __future__ import annotations

from apps.catalog.models import Product
from apps.catalog.serializers import ProductDetailSerializer
from apps.trends.models import TrendSnapshot
from apps.trends.services import VALID_HORIZONS, _label, build_radar


def build_product_detail(slug: str) -> dict:
    """Return one article with scores for every horizon and a 14-day history."""
    product = (
        Product.objects.filter(is_active=True, slug=slug)
        .select_related("category")
        .prefetch_related("sources")
        .get()
    )

    radar: dict = {}
    for horizon in VALID_HORIZONS:
        match = next(
            (row for row in build_radar(horizon=horizon) if row["product"]["slug"] == slug),
            None,
        )
        if match:
            radar[horizon] = {
                "score": match["score"],
                "demand_score": match["demand_score"],
                "supply_score": match["supply_score"],
                "momentum": match["momentum"],
                "emerging_score": match["emerging_score"],
                "label": match["label"],
                "captured_at": match["captured_at"],
            }

    history = [
        {
            "captured_at": snap.captured_at,
            "demand_score": snap.demand_score,
            "supply_score": snap.supply_score,
        }
        for snap in (
            TrendSnapshot.objects.filter(
                product=product,
                window=TrendSnapshot.Window.DAY,
            ).order_by("captured_at")[:15]
        )
    ]

    current = radar.get("now") or next(iter(radar.values()), {})
    return {
        "product": ProductDetailSerializer(product).data,
        "radar": radar,
        "history": history,
        "label": current.get("label") or _label(0, 0),
    }
