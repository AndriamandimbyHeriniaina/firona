"""Load a small Madagascar-oriented demo catalog so the radar UI is not empty.

Example:
    python manage.py seed_demo
    python manage.py seed_demo --force
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
    {
        "slug": "riz",
        "name": "Riz",
        "category": "alimentation",
        "aliases": ["vary", "riz local"],
        "scores": (78, 70, 4.0, 74, 40),
        "image_url": "/articles/riz.svg",
        "gallery": ["/articles/riz.svg", "/articles/riz-marche.svg"],
        "description": (
            "Aliment de base à Madagascar. Le radar suit surtout le riz local "
            "(vary gasy) et le riz importé quand les stocks se tendent."
        ),
        "where_to_find": (
            "Marchés d'Analakely et d'Anosibe à Tana, zoma des bassins rizicoles "
            "(Alaotra, Marovoay), épiceries de quartier et sacs de 50 kg chez les collecteurs."
        ),
    },
    {
        "slug": "huile",
        "name": "Huile de cuisine",
        "category": "alimentation",
        "aliases": ["menaka", "huile"],
        "scores": (66, 80, -3.0, 62, 28),
        "image_url": "/articles/huile.svg",
        "gallery": ["/articles/huile.svg"],
        "description": (
            "Huile de table (souvent importée). Les hausses suivent le change, "
            "le fret et les ruptures en grande surface."
        ),
        "where_to_find": (
            "Supermarchés (Score, Shoprite), épiceries, marchés d'Isotry et d'Andravoahangy. "
            "Les bidons de 5–20 L passent aussi par les grossistes."
        ),
    },
    {
        "slug": "groupe-electrogene",
        "name": "Groupe électrogène",
        "category": "energie",
        "aliases": ["groupe", "Jirama"],
        "scores": (71, 45, 14.0, 48, 82),
        "image_url": "/articles/groupe.svg",
        "gallery": ["/articles/groupe.svg"],
        "description": (
            "Demande très liée aux délestages Jirama et aux cyclones. "
            "Signal d'achat fort en saison des pluies et après les coupures longues."
        ),
        "where_to_find": (
            "Magasins d'électroménager à Tana (Behoririka, Ankorondrano), "
            "importateurs, et petites annonces consenties (pages boutiques)."
        ),
    },
    {
        "slug": "powerbank",
        "name": "Powerbank",
        "category": "telecom",
        "aliases": ["batterie externe"],
        "scores": (58, 52, 9.0, 40, 75),
        "image_url": "/articles/powerbank.svg",
        "gallery": ["/articles/powerbank.svg"],
        "description": (
            "Batterie externe pour téléphone. Monte avec les coupures et chez les étudiants / livreurs."
        ),
        "where_to_find": (
            "Boutiques télécom d'Analakely et de Soarano, kiosques GSM, "
            "pages Facebook de boutiques partenaires."
        ),
    },
    {
        "slug": "telephone",
        "name": "Téléphone",
        "category": "telecom",
        "aliases": ["findy", "smartphone", "capteur"],
        "scores": (84, 77, 6.0, 80, 55),
        "image_url": "/articles/telephone.svg",
        "gallery": ["/articles/telephone.svg", "/articles/telephone-shop.svg"],
        "description": (
            "Smartphones neufs et reconditionnés. Les Malgaches cherchent souvent "
            "par « findy » ou le modèle (Tecno, Infinix, Samsung, iPhone)."
        ),
        "where_to_find": (
            "Rues GSM d'Analakely et de Soarano, boutiques capteurs, "
            "marketplaces locales (Zoma, etc.) et pages partenaires."
        ),
    },
    {
        "slug": "lamba",
        "name": "Lamba / vêtements",
        "category": "mode",
        "aliases": ["lamba", "haody"],
        "scores": (49, 60, -6.0, 54, 22),
        "image_url": "/articles/lamba.svg",
        "gallery": ["/articles/lamba.svg"],
        "description": (
            "Lamba, haody et friperie. Le rythme suit les fêtes, la rentrée et les zoma régionaux."
        ),
        "where_to_find": (
            "Marché d'Andravoahangy, Digue, zoma de Tsiroanomandidy et Antsirabe, "
            "couturières de quartier."
        ),
    },
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
            help="Overwrite the last 15 demo days even if snapshots already exist.",
        )

    def handle(self, *args, **options):
        categories = {}
        for slug, name in CATEGORIES:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            categories[slug] = category

        source_objs = []
        for name, kind, external_id, consent in SOURCES:
            source, _ = Source.objects.update_or_create(
                kind=kind,
                external_id=external_id,
                defaults={
                    "name": name,
                    "is_active": True,
                    "consent_granted": consent,
                },
            )
            source_objs.append(source)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        today = timezone.localdate(now)

        for item in PRODUCTS:
            demand, supply, momentum, seasonal, emerging = item["scores"]
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "category": categories[item["category"]],
                    "aliases": item["aliases"],
                    "description": item["description"],
                    "image_url": item["image_url"],
                    "gallery": item["gallery"],
                    "where_to_find": item["where_to_find"],
                    "is_active": True,
                },
            )
            product.sources.set(source_objs)

            has_history = product.snapshots.exists()
            if has_history and not options["force"]:
                continue

            # One row per local day (idempotent). Demand climbs to today's value
            # when momentum is positive, and slides down to it when negative.
            for days_ago in range(14, -1, -1):
                TrendSnapshot.objects.update_or_create(
                    product=product,
                    window=TrendSnapshot.Window.DAY,
                    day=today - timedelta(days=days_ago),
                    defaults={
                        "captured_at": now - timedelta(days=days_ago),
                        "demand_score": max(0, min(100, round(demand - days_ago * momentum / 14))),
                        "supply_score": supply,
                        "momentum": momentum,
                        "seasonal_baseline": seasonal,
                        "emerging_score": emerging,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Demo radar data is ready."))
