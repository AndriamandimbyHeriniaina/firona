"""Load a small Madagascar-oriented demo catalog so the radar UI is not empty.

Example:
    python manage.py seed_demo
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.sources.models import Source
from apps.trends.models import TrendSnapshot

CATEGORIES = (
    ("alimentation", "Alimentation"),
    ("energie", "Énergie"),
    ("telecom", "Télécom"),
    ("mode", "Mode"),
)

PRODUCTS = (
    ("riz", "Riz", "alimentation", ["vary", "riz local"], 78, 70, 4.0, 74, 40),
    ("huile", "Huile de cuisine", "alimentation", ["menaka", "huile"], 66, 80, -3.0, 62, 28),
    ("groupe-electrogene", "Groupe électrogène", "energie", ["groupe", "Jirama"], 71, 45, 14.0, 48, 82),
    ("powerbank", "Powerbank", "telecom", ["batterie externe"], 58, 52, 9.0, 40, 75),
    ("telephone", "Téléphone", "telecom", ["findy", "smartphone", "capteur"], 84, 77, 6.0, 80, 55),
    ("lamba", "Lamba / vêtements", "mode", ["lamba", "haody"], 49, 60, -6.0, 54, 22),
)

SOURCES = (
    ("Meta Ads Library Madagascar", Source.Kind.META_ADS, "mg", True),
    ("Google Trends MG", Source.Kind.GOOGLE_TRENDS, "MG", True),
)


class Command(BaseCommand):
    help = "Create demo categories, products, sources, and trend snapshots."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing demo snapshots and recreate them.",
        )

    def handle(self, *args, **options):
        if Product.objects.exists() and not options["force"]:
            self.stdout.write("Demo data already present. Use --force to reseed.")
            return

        categories = {}
        for slug, name in CATEGORIES:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            categories[slug] = category

        now = timezone.now().replace(minute=0, second=0, microsecond=0)

        for slug, name, category_slug, aliases, demand, supply, momentum, seasonal, emerging in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "category": categories[category_slug],
                    "aliases": aliases,
                    "is_active": True,
                },
            )
            TrendSnapshot.objects.filter(product=product).delete()
            for days_ago in range(14, -1, -1):
                captured = now - timedelta(days=days_ago)
                drift = (14 - days_ago) * (momentum / 14)
                TrendSnapshot.objects.create(
                    product=product,
                    captured_at=captured,
                    window=TrendSnapshot.Window.DAY,
                    demand_score=max(0, min(100, int(demand - drift))),
                    supply_score=supply,
                    momentum=momentum,
                    seasonal_baseline=seasonal,
                    emerging_score=emerging,
                )

        for name, kind, external_id, consent in SOURCES:
            Source.objects.update_or_create(
                kind=kind,
                external_id=external_id,
                defaults={
                    "name": name,
                    "is_active": True,
                    "consent_granted": consent,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo radar data is ready."))
