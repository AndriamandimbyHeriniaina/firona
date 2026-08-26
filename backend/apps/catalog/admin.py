from django.contrib import admin

from apps.catalog.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
