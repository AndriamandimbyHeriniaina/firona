from django.contrib import admin

from apps.trends.models import TrendSnapshot


@admin.register(TrendSnapshot)
class TrendSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "captured_at",
        "window",
        "demand_score",
        "supply_score",
        "momentum",
        "emerging_score",
    )
    list_filter = ("window", "product__category")
    search_fields = ("product__name",)
    autocomplete_fields = ("product",)
