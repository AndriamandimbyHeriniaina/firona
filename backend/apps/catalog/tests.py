"""Article detail payload: history window, source health, demo seed shape."""

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.sources.models import Source
from apps.trends.models import TrendSnapshot


class ProductDetailTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Télécom", slug="telecom")
        self.phone = Product.objects.create(name="Téléphone", slug="telephone", category=category)
        self.source = Source.objects.create(
            name="Google Trends MG", kind=Source.Kind.GOOGLE_TRENDS, external_id="MG"
        )
        self.phone.sources.add(self.source)
        now = timezone.now()
        for days_ago in range(20):
            TrendSnapshot.objects.create(
                product=self.phone,
                captured_at=now - timedelta(days=days_ago),
                demand_score=100 - days_ago,
                supply_score=50,
                momentum=1,
                seasonal_baseline=60,
                emerging_score=30,
            )

    def test_history_is_latest_15_days_oldest_first(self):
        # v1 audit: the payload used to return the 15 *oldest* snapshots.
        body = self.client.get("/api/v1/products/telephone/").json()
        demand = [point["demand_score"] for point in body["history"]]
        self.assertEqual(demand, list(range(86, 101)))
        self.assertEqual(body["radar"]["now"]["score"], 100)
        self.assertEqual(body["radar"]["past"]["score"], 60)

    def test_sources_expose_health_not_error_text(self):
        self.source.mark_error("secret internals")
        body = self.client.get("/api/v1/products/telephone/").json()
        source = body["product"]["sources"][0]
        self.assertEqual(source["health"], "error")
        self.assertNotIn("last_error", source)

    def test_unknown_article_is_404(self):
        self.assertEqual(self.client.get("/api/v1/products/nope/").status_code, 404)


class SeedDemoTests(TestCase):
    def test_seed_is_idempotent_and_history_follows_momentum(self):
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", "--force", verbosity=0)
        phone = Product.objects.get(slug="telephone")
        snaps = list(phone.snapshots.order_by("day"))
        self.assertEqual(len(snaps), 15)
        # Positive momentum (+6): demand climbs to the configured 84 today.
        self.assertEqual(snaps[-1].demand_score, 84)
        self.assertLess(snaps[0].demand_score, snaps[-1].demand_score)
