from django.contrib import admin

from apps.trends.models import CollectedSignal, CollectionRun, TrendSnapshot


@admin.register(CollectedSignal)
class CollectedSignalAdmin(admin.ModelAdmin):
    list_display = ("day", "captured_at", "metric", "product", "source", "query", "value")
    list_filter = ("metric", "source__kind", "day")
    list_select_related = ("product", "source")
    search_fields = ("query", "product__name")
    date_hierarchy = "day"
    readonly_fields = (
        "source",
        "product",
        "captured_at",
        "day",
        "metric",
        "query",
        "value",
        "payload",
    )


@admin.register(TrendSnapshot)
class TrendSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "day",
        "captured_at",
        "window",
        "demand_score",
        "supply_score",
        "momentum",
        "emerging_score",
    )
    list_filter = ("window", "product__category")
    list_select_related = ("product",)
    search_fields = ("product__name",)
    date_hierarchy = "day"
    autocomplete_fields = ("product",)


@admin.register(CollectionRun)
class CollectionRunAdmin(admin.ModelAdmin):
    """Read-only audit trail of collector passes (retries, budgets, errors)."""

    list_display = (
        "started_at",
        "collector",
        "source",
        "status",
        "requests",
        "retries",
        "signals",
        "duration_ms",
        "detail_short",
    )
    list_filter = ("status", "collector", "source")
    list_select_related = ("source",)
    date_hierarchy = "started_at"

    def has_add_permission(self, _request):
        return False

    def has_change_permission(self, _request, _obj=None):
        return False

    @admin.display(description="Detail")
    def detail_short(self, run: CollectionRun) -> str:
        return (run.detail or "")[:80]
