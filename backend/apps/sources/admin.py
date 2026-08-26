from django.contrib import admin

from apps.sources.models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_active", "consent_granted")
    list_filter = ("kind", "is_active", "consent_granted")
    search_fields = ("name", "external_id")
