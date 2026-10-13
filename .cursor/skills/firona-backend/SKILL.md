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
- Seed via `seed_demo`. Collectors live in Celery (`collect_now` / beat), not views.
- Latest scores: order by `trends.services.LATEST_FIRST` (`-day`, `-captured_at`).
- Health: `/api/health/` (liveness), `/api/health/ready/`, `/api/v1/status/`. Status shows `health`, never error text.
- Every model change ships its migration (`MigrationDriftTests` fails otherwise).

## Do not

- Call Meta/Google from views (use Celery in v3+).
- Scrape Facebook. `consent_granted` gates Facebook-kind sources.
- Expose runserver on the host; nginx is the door.

## After change

Patch `docs/backend.md`. If URLs changed, patch `README.md` and `docs/nginx.md`.
