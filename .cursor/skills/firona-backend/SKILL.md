---
name: firona-backend
description: >-
  Implements the Firona Django API (catalog, sources, trends, admin, DRF).
  Use when editing backend/, models, serializers, views, Django settings,
  radar JSON, or manage.py commands.
---

# Firona backend

Read `docs/backend.md` before editing Django.

## Do

- Keep domain in `apps.catalog`, `apps.sources`, `apps.trends`.
- Radar: `GET /api/v1/radar/?horizon=now|past|future`.
- Trust nginx: `USE_X_FORWARDED_HOST`, `CSRF_TRUSTED_ORIGINS`.
- Seed via `seed_demo`; do not invent live Facebook data in v1.

## Do not

- Call Meta/Google from views (use Celery in v3+).
- Scrape Facebook. `consent_granted` gates Facebook-kind sources.
- Expose runserver on the host; nginx is the door.

## After change

Patch `docs/backend.md`. If URLs changed, patch `README.md` and `docs/nginx.md`.
