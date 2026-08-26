"""A scored observation of one product for a given time window.

Example:
    TrendSnapshot.objects.create(
        product=phone,
        captured_at=timezone.now(),
        window=TrendSnapshot.Window.DAY,
        demand_score=72,
        supply_score=40,
        momentum=8.5,
        seasonal_baseline=55,
        emerging_score=30,
    )
"""

from django.db import models


class TrendSnapshot(models.Model):
    class Window(models.TextChoices):
        DAY = "day", "Day"
        WEEK = "week", "Week"

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    captured_at = models.DateTimeField(db_index=True)
    window = models.CharField(max_length=8, choices=Window.choices, default=Window.DAY)
    demand_score = models.PositiveSmallIntegerField(
        help_text="0-100 score of 'cherche / mitady' style demand signals.",
    )
    supply_score = models.PositiveSmallIntegerField(
        help_text="0-100 score of listings, ads, and 'amidy' style supply signals.",
    )
    momentum = models.FloatField(
        help_text="Demand delta versus the previous window (percentage points).",
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
            models.Index(fields=["product", "captured_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.slug} @ {self.captured_at.date()} ({self.window})"
