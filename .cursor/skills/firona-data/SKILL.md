---
name: firona-data
description: >-
  Configures Firona PostgreSQL and Redis (env, volumes, Django DATABASES,
  Celery broker). Use when editing POSTGRES_*, REDIS_URL, db/redis Compose
  services, or persistence.
---

# Firona data

Read `docs/data.md` before changing stores.

## Do

- Postgres for Django. Redis for Celery only (v1).
- Credentials from env. Volume `postgres_data`.

## Do not

- Commit `.env`.
- Switch to SQLite in Compose.
- Use Redis as the product database.

## After change

Patch `docs/data.md` and `.env.example`.
