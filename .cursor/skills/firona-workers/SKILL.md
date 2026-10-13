---
name: firona-workers
description: >-
  Implements Firona Celery worker and beat (broker, tasks, schedules).
  Use when editing celery.py, tasks.py, worker/beat Compose services,
  or future collectors.
---

# Firona workers

Read `docs/workers.md` before editing Celery.

## Do

- App: `celery -A config`. Broker: `REDIS_URL`.
- Collectors: `collect_legal_sources` (beat every 6h). `assert_can_collect` before HTTP.
- Kinds: `meta_ads`, `google_trends` only. geo / country `MG`.
- HTTP only through `gated_request(..., session=CollectorSession(source))`: retries, budget, gate re-check.
- Write signals/snapshots with the per-`day` upserts (never `create` a second row for the same day).
- Wrap new collect tasks with `run_locked(...)` and `COLLECT_TASK_OPTIONS`; log each pass with `RunLog`.
- Pass errors through `redact()` before storing them.

## Do not

- Scrape Facebook/Marketplace.
- Run a collector unless `Source.is_active` (and `consent_granted` when required).
- Put long HTTP in Django request cycle; use the worker.
- Retry 4xx (other than 429) or bypass the hourly budget.
- Log request URLs with tokens (keep `httpx` at WARNING).

## After change

Patch `docs/workers.md`.
