"""Sources that Firona is allowed to read (opt-in pages, public APIs).

Example:
    Source.objects.create(
        name="Page boutique partenaire",
        kind=Source.Kind.FACEBOOK_PAGE,
        external_id="123456789",
        consent_granted=True,
    )
"""

from django.db import models


class Source(models.Model):
    class Kind(models.TextChoices):
        FACEBOOK_PAGE = "facebook_page", "Facebook page (opt-in)"
        FACEBOOK_GROUP = "facebook_group", "Facebook group (admin consent)"
        META_ADS = "meta_ads", "Meta Ads Library"
        GOOGLE_TRENDS = "google_trends", "Google Trends (MG)"
        TIKTOK = "tiktok", "TikTok public trends"
        MARKETPLACE_PARTNER = "marketplace_partner", "Local marketplace search logs"

    name = models.CharField(max_length=180)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    external_id = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)
    consent_granted = models.BooleanField(
        default=False,
        help_text="Must be true for Facebook pages/groups before any collector runs.",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "external_id"],
                condition=~models.Q(external_id=""),
                name="uniq_source_kind_external_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_kind_display()})"
