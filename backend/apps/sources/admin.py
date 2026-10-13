from django.contrib import admin

from apps.sources.models import Source


@admin.action(description="Revoke consent (stop collecting, keep history)")
def revoke_consent(_modeladmin, _request, queryset):
    for source in queryset:
        source.revoke_consent()


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "kind",
        "is_active",
        "consent_granted",
        "collectable",
        "health",
        "consecutive_failures",
        "last_success_at",
        "last_error_short",
    )
    list_filter = ("kind", "is_active", "consent_granted")
    search_fields = ("name", "external_id", "notes")
    actions = (revoke_consent,)
    readonly_fields = (
        "consent_revoked_at",
        "last_success_at",
        "last_attempt_at",
        "last_error_at",
        "last_error",
        "consecutive_failures",
        "collectable",
        "health",
    )

    @admin.display(boolean=True, description="Collectable")
    def collectable(self, source: Source) -> bool:
        return source.can_collect

    @admin.display(description="Health")
    def health(self, source: Source) -> str:
        return source.health

    @admin.display(description="Last error")
    def last_error_short(self, source: Source) -> str:
        """First 80 chars of last_error for the changelist.

        Example:
            last_error_short(source) == "META_ADS_ACCESS_TOKEN is empty..."
        """
        return (source.last_error or "")[:80]
