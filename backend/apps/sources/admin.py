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
        "last_success_at",
    )
    list_filter = ("kind", "is_active", "consent_granted")
    search_fields = ("name", "external_id", "notes")
    actions = (revoke_consent,)
    readonly_fields = ("consent_revoked_at", "last_success_at", "last_error", "collectable")

    @admin.display(boolean=True, description="Collectable")
    def collectable(self, source: Source) -> bool:
        return source.can_collect
