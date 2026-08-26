"""Tests for the legal source gate (no outbound HTTP)."""

from django.test import TestCase

from apps.sources.models import Source
from apps.sources.policy import CollectionDenied, assert_can_collect, collectable_sources


class SourcePolicyTests(TestCase):
    def test_trends_is_collectable(self):
        source = Source.objects.create(
            name="Google Trends MG",
            kind=Source.Kind.GOOGLE_TRENDS,
            external_id="MG",
            is_active=True,
            consent_granted=True,
        )
        assert_can_collect(source)
        self.assertTrue(source.can_collect)

    def test_facebook_page_blocked_even_with_consent(self):
        source = Source.objects.create(
            name="Page partenaire",
            kind=Source.Kind.FACEBOOK_PAGE,
            external_id="1",
            is_active=True,
            consent_granted=True,
        )
        with self.assertRaises(CollectionDenied):
            assert_can_collect(source)
        self.assertIn("not enabled", source.block_reason or "")

    def test_inactive_ads_blocked(self):
        source = Source.objects.create(
            name="Ads",
            kind=Source.Kind.META_ADS,
            external_id="mg",
            is_active=False,
            consent_granted=True,
        )
        with self.assertRaises(CollectionDenied):
            assert_can_collect(source)

    def test_revoke_stops_collect_and_keeps_row(self):
        source = Source.objects.create(
            name="Ads",
            kind=Source.Kind.META_ADS,
            external_id="mg-2",
            is_active=True,
            consent_granted=True,
        )
        source.revoke_consent()
        source.refresh_from_db()
        self.assertFalse(source.can_collect)
        self.assertIsNotNone(source.consent_revoked_at)
        self.assertTrue(Source.objects.filter(pk=source.pk).exists())

    def test_collectable_sources_only_enabled_kinds(self):
        Source.objects.create(
            name="Trends",
            kind=Source.Kind.GOOGLE_TRENDS,
            external_id="MG-x",
            is_active=True,
        )
        Source.objects.create(
            name="Page",
            kind=Source.Kind.FACEBOOK_PAGE,
            external_id="9",
            is_active=True,
            consent_granted=True,
        )
        names = [item.name for item in collectable_sources()]
        self.assertEqual(names, ["Trends"])
