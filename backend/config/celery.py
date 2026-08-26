"""Celery application used by the worker and beat Compose services.

Example:
    celery -A config worker -l info
    celery -A config beat -l info
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("firona")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
