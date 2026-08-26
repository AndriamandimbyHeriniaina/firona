"""Django project package for the Firona API.

Expose the Celery app so `celery -A config` discovers it.
"""

from config.celery import app as celery_app

__all__ = ("celery_app",)
