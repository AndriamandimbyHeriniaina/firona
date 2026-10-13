"""Trend scores, raw signals from legal collectors, and collect run logs.

Example:
    TrendSnapshot.objects.update_or_create(
        product=phone,
        window=TrendSnapshot.Window.DAY,
        day=timezone.localdate(),
        defaults={
            "captured_at": timezone.now(),
            "demand_score": 72,
            "supply_score": 40,
            "momentum": 8.5,
            "seasonal_baseline": 55,
            "emerging_score": 30,
        },
    )
"""

from django.db import models
from django.utils import timezone


def _fill_day(instance) -> None:
    """Default `day` to the local (Antananarivo) date of `captured_at`."""
    if instance.day is None and instance.captured_at is not None:
        instance.day = timezone.localdate(instance.captured_at)


class CollectedSignal(models.Model):
    """Raw legal-source observation before scores are derived.

    One row per source × product × metric × local day: re-running a collector
    the same day updates the row instead of duplicating it.

    Example:
        CollectedSignal.objects.create(
            source=trends_mg,
            product=phone,
            captured_at=timezone.now(),
            day=timezone.localdate(),
            metric=CollectedSignal.Metric.TREND_MATCH,
            query="findy",
            value=1,
            payload={"titles": ["findy tecno"], "rank": 1},
        )
    """

    class Metric(models.TextChoices):
        ADS_MATCH = "ads_match", "Ads Library match"
        TREND_MATCH = "trend_match", "Google Trends MG match"

    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.CASCADE,
        related_name="signals",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="collected_signals",
    )
    captured_at = models.DateTimeField(
        db_index=True,
        help_text="Last time this day's signal was observed.",
    )
    day = models.DateField(help_text="Local date (Indian/Antananarivo) of the observation.")
    metric = models.CharField(max_length=32, choices=Metric.choices)
    query = models.CharField(max_length=180)
    value = models.FloatField(
        help_text="Ads hit count, or best Trends rank of the day (1 = hottest).",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Public ids / titles only. No creative bodies, phones, or comments.",
    )

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["product", "captured_at"], name="trends_coll_product_capt_idx"),
            models.Index(fields=["source", "captured_at"], name="trends_coll_source_capt_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "product", "metric", "day"],
                name="uniq_signal_source_product_metric_day",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.metric} {self.product_id}={self.value} ({self.day})"

    def save(self, *args, **kwargs):
        _fill_day(self)
        super().save(*args, **kwargs)


class TrendSnapshot(models.Model):
    """Radar scores for one product and one window (one DAY row per local date)."""

    class Window(models.TextChoices):
        DAY = "day", "Day"
        WEEK = "week", "Week"

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    captured_at = models.DateTimeField(db_index=True)
    day = models.DateField(help_text="Local date the scores describe (idempotency key).")
    window = models.CharField(max_length=8, choices=Window.choices, default=Window.DAY)
    demand_score = models.PositiveSmallIntegerField(
        help_text="0-100 score of 'cherche / mitady' style demand signals.",
    )
    supply_score = models.PositiveSmallIntegerField(
        help_text="0-100 score of listings, ads, and 'amidy' style supply signals.",
    )
    momentum = models.FloatField(
        help_text="Demand delta versus the previous day (points).",
    )
    seasonal_baseline = models.PositiveSmallIntegerField(
        help_text="Typical demand for this calendar week, used for the past radar.",
    )
    emerging_score = models.PositiveSmallIntegerField(
        help_text="0-100 likelihood the product is heating up (future radar).",
    )

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["product", "captured_at"], name="trends_snap_product_capt_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "window", "day"],
                name="uniq_snapshot_product_window_day",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_id} @ {self.day} ({self.window})"

    def save(self, *args, **kwargs):
        _fill_day(self)
        super().save(*args, **kwargs)


class CollectionRun(models.Model):
    """One collector pass over one source: the audit trail behind /api/v1/status/.

    Example:
        CollectionRun.objects.filter(source=ads, status="error")[:5]
    """

    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        OK = "ok", "OK"
        ERROR = "error", "Error"
        SKIPPED = "skipped", "Skipped (gate / config)"

    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.CASCADE,
        related_name="runs",
    )
    collector = models.CharField(max_length=40)
    started_at = models.DateTimeField(db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    requests = models.PositiveIntegerField(default=0, help_text="HTTP attempts, retries included.")
    retries = models.PositiveIntegerField(default=0)
    signals = models.PositiveIntegerField(default=0, help_text="Signal rows written or updated.")
    duration_ms = models.PositiveIntegerField(default=0)
    detail = models.TextField(blank=True, help_text="Redacted error or skip reason.")

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["source", "started_at"], name="trends_run_source_started_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.collector} {self.status} @ {self.started_at:%Y-%m-%d %H:%M}"
