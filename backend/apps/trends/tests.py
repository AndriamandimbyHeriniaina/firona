"""Collector tests: legal gate before HTTP, MG-only, no new Product rows."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings

from apps.catalog.models import Category, Product
from apps.sources.models import Source
from apps.sources.policy import CollectionDenied
from apps.trends.collectors.google_trends import collect_google_trends, parse_trends_rss
from apps.trends.collectors.http import gated_request
from apps.trends.collectors.matching import match_title_to_product, normalize
from apps.trends.collectors.meta_ads import collect_meta_ads
from apps.trends.collectors.scoring import refresh_snapshots_from_signals
from apps.trends.models import CollectedSignal, TrendSnapshot
from apps.trends.tasks import refresh_radar_snapshots

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
  <channel>
    <item>
      <title>findy tecno analakely</title>
      <ht:approx_traffic>2,000+</ht:approx_traffic>
    </item>
    <item>
      <title>vary gasy</title>
      <ht:approx_traffic>500+</ht:approx_traffic>
    </item>
    <item>
      <title>unrelated football score</title>
      <ht:approx_traffic>100+</ht:approx_traffic>
    </item>
  </channel>
</rss>
"""


class RssParserTests(SimpleTestCase):
    def test_parse_titles_and_ranks(self):
        rows = parse_trends_rss(RSS_FIXTURE)
        self.assertEqual(rows[0]["title"], "findy tecno analakely")
        self.assertEqual(rows[0]["rank"], 1)
        self.assertEqual(rows[0]["traffic_value"], 2000.0)
        self.assertEqual(len(rows), 3)


class CollectorTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Télécom", slug="telecom")
        self.phone = Product.objects.create(
            name="Téléphone",
            slug="telephone",
            category=self.category,
            aliases=["findy", "smartphone"],
        )
        self.riz = Product.objects.create(
            name="Riz",
            slug="riz",
            category=self.category,
            aliases=["vary", "riz local"],
        )
        self.trends = Source.objects.create(
            name="Google Trends MG",
            kind=Source.Kind.GOOGLE_TRENDS,
            external_id="MG",
            is_active=True,
        )
        self.ads = Source.objects.create(
            name="Meta Ads Library Madagascar",
            kind=Source.Kind.META_ADS,
            external_id="mg",
            is_active=True,
        )
        self.phone.sources.add(self.trends, self.ads)
        self.riz.sources.add(self.trends, self.ads)

    def test_match_aliases_does_not_invent_products(self):
        matched = match_title_to_product("prix findy", [self.phone, self.riz])
        self.assertEqual(matched[0], self.phone)
        self.assertIsNone(match_title_to_product("unrelated football score", [self.phone, self.riz]))

    @patch("apps.trends.collectors.http.httpx.Client")
    def test_gated_request_skips_http_when_facebook(self, client_cls):
        page = Source.objects.create(
            name="Page partenaire",
            kind=Source.Kind.FACEBOOK_PAGE,
            external_id="1",
            is_active=True,
            consent_granted=True,
        )
        with self.assertRaises(CollectionDenied):
            gated_request(page, "GET", "https://example.test/ads")
        client_cls.assert_not_called()

    def test_trends_geo_fr_is_denied_without_http(self):
        self.trends.external_id = "FR"
        self.trends.save()
        with patch("apps.trends.collectors.google_trends.gated_request") as gated:
            result = collect_google_trends()
        gated.assert_not_called()
        self.assertEqual(result["skipped"], 1)

    def test_inactive_ads_never_http(self):
        self.ads.is_active = False
        self.ads.save()
        with patch("apps.trends.collectors.meta_ads.gated_request") as gated:
            with override_settings(META_ADS_ACCESS_TOKEN="secret"):
                collect_meta_ads()
        gated.assert_not_called()

    @override_settings(META_ADS_ACCESS_TOKEN="")
    def test_missing_ads_token_marks_error_without_http(self):
        with patch("apps.trends.collectors.meta_ads.gated_request") as gated:
            result = collect_meta_ads()
        gated.assert_not_called()
        self.ads.refresh_from_db()
        self.assertIn("META_ADS_ACCESS_TOKEN", self.ads.last_error)
        self.assertFalse(result["ok"])

    def test_google_trends_stores_matches_only(self):
        response = MagicMock()
        response.status_code = 200
        response.text = RSS_FIXTURE
        with patch(
            "apps.trends.collectors.google_trends.gated_request",
            return_value=response,
        ) as gated:
            result = collect_google_trends()
        gated.assert_called_once()
        self.assertEqual(gated.call_args.kwargs["params"], {"geo": "MG"})
        self.assertEqual(result["signals"], 2)
        self.assertEqual(result["unmatched"], 1)
        self.assertEqual(CollectedSignal.objects.count(), 2)
        self.assertEqual(Product.objects.count(), 2)
        self.trends.refresh_from_db()
        self.assertEqual(self.trends.last_error, "")
        self.assertIsNotNone(self.trends.last_success_at)

    @override_settings(META_ADS_ACCESS_TOKEN="test-token")
    def test_meta_ads_stores_public_ids_not_bodies(self):
        response = MagicMock()
        response.status_code = 200
        response.text = "{}"
        response.json.return_value = {"data": [{"id": "111"}, {"id": "222"}]}
        with patch(
            "apps.trends.collectors.meta_ads.gated_request",
            return_value=response,
        ):
            result = collect_meta_ads()
        self.assertTrue(result["ok"])
        signal = CollectedSignal.objects.get(product=self.phone)
        self.assertEqual(signal.payload["ad_ids"], ["111", "222"])
        self.assertNotIn("ad_creative_bodies", signal.payload)

    def test_refresh_snapshots_only_for_signaled_products(self):
        from django.utils import timezone

        captured = timezone.now()
        CollectedSignal.objects.create(
            source=self.trends,
            product=self.phone,
            captured_at=captured,
            metric=CollectedSignal.Metric.TREND_MATCH,
            query="findy",
            value=1,
            payload={"title": "findy tecno", "rank": 1, "geo": "MG"},
        )
        TrendSnapshot.objects.create(
            product=self.riz,
            captured_at=captured,
            demand_score=70,
            supply_score=60,
            momentum=0,
            seasonal_baseline=70,
            emerging_score=20,
        )
        result = refresh_snapshots_from_signals(now=captured)
        self.assertEqual(result["wrote"], 1)
        phone_snap = TrendSnapshot.objects.get(product=self.phone, captured_at=captured)
        self.assertEqual(phone_snap.demand_score, 100)
        self.assertEqual(TrendSnapshot.objects.filter(product=self.riz).count(), 1)

    def test_match_whole_words_only(self):
        # v3 audit: substring matching found "riz" inside "prize".
        self.assertIsNone(match_title_to_product("prize money winners", [self.phone, self.riz]))
        self.assertIsNone(match_title_to_product("findyx", [self.phone, self.riz]))

    def test_match_is_accent_insensitive_and_prefers_longest_term(self):
        self.assertEqual(normalize("  Téléphone, pas cher! "), "telephone pas cher")
        matched = match_title_to_product("TELEPHONE pas cher", [self.phone, self.riz])
        self.assertEqual(matched[0], self.phone)
        product, term = match_title_to_product("prix riz local tsena", [self.phone, self.riz])
        self.assertEqual((product, term), (self.riz, "riz local"))

    def test_short_title_matches_whole_word_of_alias(self):
        product, _term = match_title_to_product("riz", [self.phone, self.riz])
        self.assertEqual(product, self.riz)
        self.assertIsNone(match_title_to_product("ri", [self.phone, self.riz]))

    def test_refresh_task_uses_today_not_exact_timestamp(self):
        # v3 audit: the task passed a fresh now() and matched no signal.
        from django.utils import timezone

        CollectedSignal.objects.create(
            source=self.trends,
            product=self.phone,
            captured_at=timezone.now(),
            metric=CollectedSignal.Metric.TREND_MATCH,
            query="findy",
            value=2,
            payload={"titles": ["findy"], "rank": 2},
        )
        result = refresh_radar_snapshots()
        self.assertEqual(result["wrote"], 1)
        self.assertEqual(TrendSnapshot.objects.get(product=self.phone).demand_score, 95)
