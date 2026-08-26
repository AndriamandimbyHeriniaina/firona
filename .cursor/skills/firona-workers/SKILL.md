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
- v1: `ping_stack` only. Collectors start in v3 on **legal** sources.

## Do not

- Scrape Facebook/Marketplace.
- Run a collector unless `Source.is_active` (and `consent_granted` when required).
- Put long HTTP in Django request cycle; use the worker.

## After change

Patch `docs/workers.md`.
