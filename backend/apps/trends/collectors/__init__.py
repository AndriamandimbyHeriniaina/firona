"""v3 legal collectors: Ads Library + Google Trends MG, behind assert_can_collect.

Example:
    from apps.trends.collectors import collect_legal_sources
    collect_legal_sources()
"""

from django.utils import timezone

from apps.trends.collectors.google_trends import collect_google_trends
from apps.trends.collectors.meta_ads import collect_meta_ads
from apps.trends.collectors.scoring import refresh_snapshots_from_signals


def collect_legal_sources() -> dict:
    """Run both HTTP collectors then write TrendSnapshot rows for matched products.

    Example:
        result = collect_legal_sources()
        # {"trends": {...}, "ads": {...}, "snapshots": {"wrote": 2}}
    """
    now = timezone.now()
    trends = collect_google_trends(now=now)
    ads = collect_meta_ads(now=now)
    snapshots = refresh_snapshots_from_signals(now=now)
    return {"trends": trends, "ads": ads, "snapshots": snapshots}
