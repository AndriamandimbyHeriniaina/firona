"""Assemble the article detail payload (catalog + radar + history).

Example:
    from apps.catalog.services import build_product_detail
    payload = build_product_detail("telephone")
"""

from __future__ import annotations

from apps.catalog.models import Product
from apps.catalog.serializers import ProductDetailSerializer
from apps.trends.models import TrendSnapshot
from apps.trends.services import LATEST_FIRST, product_radar, trend_label

HISTORY_DAYS = 15


def build_product_detail(slug: str) -> dict:
    """Return one article with scores for every horizon and its latest 15 daily points."""
    product = (
        Product.objects.filter(is_active=True, slug=slug)
        .select_related("category")
        .prefetch_related("sources")
        .get()
    )

    radar = product_radar(product)

    recent = list(
        TrendSnapshot.objects.filter(product=product, window=TrendSnapshot.Window.DAY)
        .order_by(*LATEST_FIRST)
        .values("captured_at", "demand_score", "supply_score")[:HISTORY_DAYS]
    )
    history = list(reversed(recent))  # oldest → newest for the chart

    current = radar.get("now") or {}
    return {
        "product": ProductDetailSerializer(product).data,
        "radar": radar,
        "history": history,
        "label": current.get("label") or trend_label(0, 0),
    }
