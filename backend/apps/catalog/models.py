"""Catalog models: categories and products (articles) tracked by Firona.

Example:
    phone = Product.objects.create(
        name="Téléphone",
        slug="telephone",
        category=electronics,
        aliases=["findy", "smartphone", "capteur"],
    )
"""

from django.db import models


class Category(models.Model):
    """High-level grouping used to filter the radar (food, energy, fashion...)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """An article whose demand we estimate from consented social sources."""

    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    aliases = models.JSONField(
        default=list,
        blank=True,
        help_text='Search variants, e.g. ["findy", "smartphone"].',
    )
    description = models.TextField(
        blank=True,
        help_text="Short article blurb shown on the detail screen.",
    )
    image_url = models.CharField(
        max_length=300,
        blank=True,
        help_text='Hero image path, e.g. "/articles/riz.svg".',
    )
    gallery = models.JSONField(
        default=list,
        blank=True,
        help_text='Extra image paths, e.g. ["/articles/riz-marche.svg"].',
    )
    where_to_find = models.TextField(
        blank=True,
        help_text="Where buyers typically find the article in Madagascar.",
    )
    sources = models.ManyToManyField(
        "sources.Source",
        blank=True,
        related_name="products",
        help_text="Legal data sources that feed this article's radar.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
