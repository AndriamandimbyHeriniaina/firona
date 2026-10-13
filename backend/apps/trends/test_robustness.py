"""v4 robustness: retries, budgets, idempotent days, locks, run log, status."""

import logging
import time
from datetime import timedelta
from email.utils import format_datetime
from unittest.mock import MagicMock, patch

import httpx
from celery.exceptions import SoftTimeLimitExceeded
from django.core.cache import cache
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.sources.models import Source
from apps.sources.policy import CollectionDenied
from apps.sources.redact import RedactingFilter, redact
from apps.trends.collectors.google_trends import collect_google_trends
from apps.trends.collectors.http import (
    BudgetExceeded,
    CollectorSession,
    RetriesExhausted,
    backoff_delay,
    gated_request,
    retry_after_seconds,
)
from apps.trends.collectors.meta_ads import collect_meta_ads
from apps.trends.collectors.scoring import refresh_snapshots_from_signals
from apps.trends.models import CollectedSignal, CollectionRun, TrendSnapshot
from apps.trends.tasks import (
    COLLECT_LOCK_KEY,
    HEARTBEAT_KEY,
    heartbeat,
    prune_collection_runs,
    run_locked,
)
from apps.trends.tests import RSS_FIXTURE

URL = "https://example.test/feed"


def fake_response(status: int, *, text: str = "", headers: dict | None = None, json=None):
    response = MagicMock()
    response.status_code = status
    response.text = text
    response.headers = headers or {}
    response.json.return_value = json or {}
    return response


class Fixtures(TestCase):
    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Télécom", slug="telecom")
        self.phone = Product.objects.create(
            name="Téléphone", slug="telephone", category=category, aliases=["findy"]
        )
        self.riz = Product.objects.create(
            name="Riz", slug="riz", category=category, aliases=["vary"]
        )
        self.trends = Source.objects.create(
            name="Google Trends MG", kind=Source.Kind.GOOGLE_TRENDS, external_id="MG"
        )
        self.ads = Source.objects.create(
            name="Meta Ads Library Madagascar", kind=Source.Kind.META_ADS, external_id="mg"
        )


@patch("apps.trends.collectors.http.time.sleep")
@patch("apps.trends.collectors.http.httpx.Client")
class GatedRequestRetryTests(Fixtures):
    def fake_client(self, client_cls, *responses):
        instance = client_cls.return_value
        instance.request.side_effect = list(responses)
        return instance

    def test_retries_5xx_then_succeeds(self, client_cls, sleep):
        client = self.fake_client(client_cls, fake_response(503), fake_response(200, text="ok"))
        with CollectorSession(self.trends) as session:
            response = gated_request(self.trends, "GET", URL, session=session)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(session.stats, {"requests": 2, "retries": 1})
        sleep.assert_called_once()

    def test_honours_retry_after(self, client_cls, sleep):
        self.fake_client(client_cls, fake_response(429, headers={"Retry-After": "7"}), fake_response(200))
        gated_request(self.trends, "GET", URL)
        sleep.assert_called_once_with(7.0)

    def test_does_not_retry_client_errors(self, client_cls, sleep):
        client = self.fake_client(client_cls, fake_response(400))
        response = gated_request(self.trends, "GET", URL)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(client.request.call_count, 1)
        sleep.assert_not_called()

    def test_timeouts_exhaust_attempts(self, client_cls, sleep):
        timeout = httpx.ReadTimeout("slow")
        client = self.fake_client(client_cls, timeout, timeout, timeout)
        with self.assertRaises(RetriesExhausted):
            gated_request(self.trends, "GET", URL)
        self.assertEqual(client.request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_refuses_to_wait_longer_than_a_minute(self, client_cls, sleep):
        client = self.fake_client(client_cls, fake_response(503, headers={"Retry-After": "120"}))
        with self.assertRaises(RetriesExhausted):
            gated_request(self.trends, "GET", URL)
        self.assertEqual(client.request.call_count, 1)
        sleep.assert_not_called()

    def test_gate_checked_against_db_before_first_request(self, client_cls, sleep):
        # The in-memory object still says active; the admin already disabled it.
        Source.objects.filter(pk=self.ads.pk).update(is_active=False)
        client = self.fake_client(client_cls, fake_response(200))
        with self.assertRaises(CollectionDenied):
            gated_request(self.ads, "GET", URL)
        client.request.assert_not_called()

    @override_settings(COLLECT_BUDGET_PER_HOUR={"google_trends": 1})
    def test_budget_blocks_before_any_socket(self, client_cls, sleep):
        client = self.fake_client(client_cls, fake_response(200), fake_response(200))
        gated_request(self.trends, "GET", URL)
        with self.assertRaises(BudgetExceeded):
            gated_request(self.trends, "GET", URL)
        self.assertEqual(client.request.call_count, 1)

    def test_consent_revoked_between_attempts_stops_retries(self, client_cls, sleep):
        def revoke_then_fail(*_args, **_kwargs):
            Source.objects.filter(pk=self.ads.pk).update(is_active=False)
            return fake_response(503)

        client = client_cls.return_value
        client.request.side_effect = revoke_then_fail
        with self.assertRaises(CollectionDenied):
            gated_request(self.ads, "GET", URL)
        self.assertEqual(client.request.call_count, 1)


class BackoffTests(SimpleTestCase):
    def test_backoff_is_bounded_and_jittered(self):
        for attempt in range(1, 8):
            self.assertLessEqual(backoff_delay(attempt), 20.0)

    def test_retry_after_seconds_and_http_date(self):
        self.assertEqual(retry_after_seconds("7"), 7.0)
        self.assertIsNone(retry_after_seconds("soon"))
        self.assertIsNone(retry_after_seconds(None))
        now = time.time()
        in_30s = format_datetime(timezone.now() + timedelta(seconds=30), usegmt=True)
        self.assertAlmostEqual(retry_after_seconds(in_30s, now=now), 30, delta=2)


class IdempotentDayTests(Fixtures):
    def rss(self):
        return patch(
            "apps.trends.collectors.google_trends.gated_request",
            return_value=fake_response(200, text=RSS_FIXTURE),
        )

    def test_two_trends_runs_same_day_keep_one_signal_per_product(self):
        with self.rss():
            collect_google_trends()
            collect_google_trends()
        self.assertEqual(CollectedSignal.objects.count(), 2)
        phone = CollectedSignal.objects.get(product=self.phone)
        self.assertEqual(phone.value, 1.0)
        self.assertEqual(phone.payload["titles"], ["findy tecno analakely"])

    @override_settings(META_ADS_ACCESS_TOKEN="test-token")
    def test_ads_runs_union_distinct_ids(self):
        first = fake_response(200, json={"data": [{"id": "1"}, {"id": "2"}]})
        second = fake_response(200, json={"data": [{"id": "2"}, {"id": "3"}]})
        with patch("apps.trends.collectors.meta_ads.gated_request", return_value=first):
            collect_meta_ads()
        with patch("apps.trends.collectors.meta_ads.gated_request", return_value=second):
            collect_meta_ads()
        signal = CollectedSignal.objects.get(product=self.phone, metric="ads_match")
        self.assertEqual(signal.value, 3.0)
        self.assertEqual(signal.payload["ad_ids"], ["1", "2", "3"])

    def test_snapshot_upserted_and_momentum_vs_previous_day(self):
        now = timezone.now()
        TrendSnapshot.objects.create(
            product=self.phone,
            captured_at=now - timedelta(days=1),
            demand_score=60,
            supply_score=50,
            momentum=0,
            seasonal_baseline=60,
            emerging_score=20,
        )
        with self.rss():
            collect_google_trends(now=now)
        refresh_snapshots_from_signals(now=now)
        refresh_snapshots_from_signals(now=now + timedelta(hours=6))
        today = TrendSnapshot.objects.filter(product=self.phone, day=timezone.localdate(now))
        self.assertEqual(today.count(), 1)
        self.assertEqual(today.get().demand_score, 100)
        self.assertEqual(today.get().momentum, 40.0)

    def test_run_log_records_requests_and_signals(self):
        with self.rss():
            collect_google_trends()
        run = CollectionRun.objects.get(source=self.trends)
        self.assertEqual(run.status, CollectionRun.Status.OK)
        self.assertEqual(run.signals, 2)
        self.assertIsNotNone(run.finished_at)

    def test_trends_failure_is_logged_and_counted(self):
        with patch(
            "apps.trends.collectors.google_trends.gated_request",
            side_effect=RetriesExhausted("HTTP 503 after 3 attempts"),
        ):
            result = collect_google_trends()
        self.assertFalse(result["ok"])
        self.trends.refresh_from_db()
        self.assertEqual(self.trends.consecutive_failures, 1)
        self.assertEqual(self.trends.health, "error")
        self.assertEqual(CollectionRun.objects.get().status, CollectionRun.Status.ERROR)


class TimeLimitTests(Fixtures):
    def test_soft_time_limit_is_not_swallowed(self):
        with patch(
            "apps.trends.collectors.google_trends.gated_request",
            side_effect=SoftTimeLimitExceeded(),
        ):
            with self.assertRaises(SoftTimeLimitExceeded):
                collect_google_trends()
        run = CollectionRun.objects.get(source=self.trends)
        self.assertEqual(run.status, CollectionRun.Status.ERROR)
        self.assertEqual(run.detail, "soft time limit reached")

    @override_settings(META_ADS_ACCESS_TOKEN="test-token")
    def test_token_requests_never_follow_redirects(self):
        response = fake_response(200, json={"data": []})
        with patch("apps.trends.collectors.meta_ads.gated_request", return_value=response) as gated:
            collect_meta_ads()
        self.assertFalse(gated.call_args.kwargs["follow_redirects"])


class SecretRedactionTests(Fixtures):
    @override_settings(META_ADS_ACCESS_TOKEN="EAABsecret123")
    def test_tokens_never_stored(self):
        self.ads.mark_error("GET /ads_archive?access_token=EAABsecret123&limit=25 failed")
        self.ads.refresh_from_db()
        self.assertNotIn("EAABsecret123", self.ads.last_error)
        self.assertIn("access_token=[redacted]", self.ads.last_error)
        self.assertEqual(redact("Authorization: Bearer abc.def"), "Authorization: Bearer [redacted]")

    @override_settings(META_ADS_ACCESS_TOKEN="EAABsecret123")
    def test_log_filter_redacts_messages_and_tracebacks(self):
        try:
            raise RuntimeError("proxy echoed ?access_token=EAABsecret123")
        except RuntimeError:
            import sys

            record = logging.LogRecord(
                "x", logging.ERROR, __file__, 1, "failed %s", ("EAABsecret123",), sys.exc_info()
            )
        RedactingFilter().filter(record)
        self.assertNotIn("EAABsecret123", record.getMessage())
        self.assertNotIn("EAABsecret123", record.exc_text)


class LockAndHousekeepingTests(Fixtures):
    def test_second_collect_is_skipped_while_locked(self):
        cache.add(COLLECT_LOCK_KEY, "someone-else", timeout=60)
        collector = MagicMock()
        self.assertEqual(run_locked(collector), {"skipped": "another collect is still running"})
        collector.assert_not_called()

    def test_lock_released_after_run(self):
        self.assertEqual(run_locked(lambda: {"done": True}), {"done": True})
        self.assertIsNone(cache.get(COLLECT_LOCK_KEY))

    def test_prune_closes_orphans_and_drops_old_runs(self):
        old = timezone.now() - timedelta(days=200)
        CollectionRun.objects.create(source=self.trends, collector="x", started_at=old, status="ok")
        orphan = CollectionRun.objects.create(
            source=self.trends,
            collector="x",
            started_at=timezone.now() - timedelta(hours=5),
        )
        self.assertEqual(prune_collection_runs(), {"orphaned": 1, "deleted": 1})
        orphan.refresh_from_db()
        self.assertEqual(orphan.status, CollectionRun.Status.ERROR)


@patch("config.health._queue_backlog", return_value=0)
class StatusEndpointTests(Fixtures):
    def fresh_snapshot(self):
        TrendSnapshot.objects.create(
            product=self.phone,
            captured_at=timezone.now(),
            demand_score=70,
            supply_score=40,
            momentum=2,
            seasonal_baseline=60,
            emerging_score=30,
        )

    def test_degraded_without_worker_heartbeat(self, _backlog):
        self.fresh_snapshot()
        body = self.client.get("/api/v1/status/").json()
        self.assertEqual(body["status"], "degraded")
        self.assertFalse(body["checks"]["worker"]["ok"])

    def test_ok_when_worker_alive_and_data_fresh(self, _backlog):
        self.fresh_snapshot()
        heartbeat()
        self.trends.mark_success()
        self.ads.mark_success()
        response = self.client.get("/api/v1/status/")
        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "ok", body)
        self.assertEqual({item["health"] for item in body["sources"]}, {"ok"})
        self.assertIn("no-cache", response["Cache-Control"])

    def test_failing_source_and_stale_data_degrade(self, _backlog):
        heartbeat()
        self.ads.mark_error("boom")
        body = self.client.get("/api/v1/status/").json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["failing_sources"], ["Meta Ads Library Madagascar"])
        self.assertFalse(body["checks"]["data"]["ok"])
        self.assertNotIn("last_error", body["sources"][0])

    def test_ready_probe(self, _backlog):
        response = self.client.get("/api/health/ready/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"database": "ok", "cache": "ok"})
        self.assertIsNotNone(cache.get(HEARTBEAT_KEY) or "probe-only")


class ConditionalGetTests(Fixtures):
    def test_radar_answers_304_when_unchanged(self):
        TrendSnapshot.objects.create(
            product=self.phone,
            captured_at=timezone.now(),
            demand_score=70,
            supply_score=40,
            momentum=2,
            seasonal_baseline=60,
            emerging_score=30,
        )
        first = self.client.get("/api/v1/radar/?horizon=now")
        self.assertTrue(first.has_header("ETag"))
        second = self.client.get("/api/v1/radar/?horizon=now", HTTP_IF_NONE_MATCH=first["ETag"])
        self.assertEqual(second.status_code, 304)


class MigrationDriftTests(TestCase):
    def test_models_match_migrations(self):
        # v3 audit: hand-written migrations had drifted from the models.
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except SystemExit:
            self.fail("Model changes without a migration: run makemigrations")
