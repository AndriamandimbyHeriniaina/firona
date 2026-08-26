"""Sources that Firona is allowed to read (opt-in pages, public APIs).

Example:
    page = Source.objects.create(
        name="Page boutique partenaire",
        kind=Source.Kind.FACEBOOK_PAGE,
        external_id="123456789",
        consent_granted=True,
    )
    page.can_collect  # False until that kind is enabled for collectors
"""

from django.db import models
from django.utils import timezone


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
        help_text="Required for Facebook pages/groups and marketplace partners.",
    )
    consent_revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When set, collectors must stop. Historical snapshots are kept.",
    )
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Partner outreach, admin name, contract reference — not user PII from posts.",
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

    @property
    def requires_consent(self) -> bool:
        from apps.sources.policy import CONSENT_REQUIRED_KINDS

        return self.kind in CONSENT_REQUIRED_KINDS

    @property
    def can_collect(self) -> bool:
        return self.block_reason is None

    @property
    def block_reason(self) -> str | None:
        """Human-readable why this source must not be fetched, or None if allowed."""
        from apps.sources.policy import COLLECTABLE_KINDS, CONSENT_REQUIRED_KINDS

        if self.kind not in COLLECTABLE_KINDS:
            return f"kind {self.kind} is not enabled for collectors yet"
        if not self.is_active:
            return "source is inactive"
        if self.consent_revoked_at is not None:
            return "consent was revoked"
        if self.kind in CONSENT_REQUIRED_KINDS and not self.consent_granted:
            return "consent is required and was not granted"
        return None

    def revoke_consent(self) -> None:
        """Stop future collects; keep existing TrendSnapshot rows."""
        self.consent_granted = False
        self.consent_revoked_at = timezone.now()
        self.is_active = False
        self.save(
            update_fields=["consent_granted", "consent_revoked_at", "is_active"]
        )

    def mark_success(self) -> None:
        self.last_success_at = timezone.now()
        self.last_error = ""
        self.save(update_fields=["last_success_at", "last_error"])

    def mark_error(self, message: str) -> None:
        self.last_error = message[:2000]
        self.save(update_fields=["last_error"])
