"""Run the legal collectors once from the Django container.

Uses the same lock as the beat task, so it never overlaps a scheduled run.

Example:
    python manage.py collect_now
    docker compose exec backend python manage.py collect_now
"""

from django.core.management.base import BaseCommand

from apps.trends.collectors import collect_legal_sources
from apps.trends.tasks import run_locked


class Command(BaseCommand):
    help = "Fetch Ads Library + Google Trends MG and upsert today's TrendSnapshot rows."

    def handle(self, *args, **options):
        result = run_locked(collect_legal_sources)
        self.stdout.write(self.style.SUCCESS(str(result)))
