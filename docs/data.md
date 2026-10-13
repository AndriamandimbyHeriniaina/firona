# Data stores

| Service | Image | Role | Compose port |
| --- | --- | --- | --- |
| `db` | postgres:16-alpine | Django database | 5432 (dev only) |
| `redis` | redis:7-alpine | Celery broker + result backend | 6379 (dev only) |

Django reads `POSTGRES_*`. Celery reads `REDIS_URL` (default `redis://redis:6379/0`).

Django's cache uses Redis **DB 1** (`REDIS_CACHE_URL`, default `redis://redis:6379/1`, key prefix `firona`) so it never mixes with the broker queues:

| Key | Use |
| --- | --- |
| `firona:lock:collect` | Single-flight lock for collects |
| `firona:budget:<source>:<YYYYMMDDHH>` | Hourly request budget per source |
| `firona:heartbeat:worker` | Last worker heartbeat (status endpoint) |

Tests use an in-memory cache (`TESTING` in settings), never the live Redis.

`TrendSnapshot` is unique per (product, window, `day`) and `CollectedSignal` per (source, product, metric, `day`). `CollectionRun` rows are pruned after `COLLECT_RUN_RETENTION_DAYS` (90).

Volume `postgres_data` survives `docker compose down`.

Do not put secrets in git. Change `POSTGRES_PASSWORD` outside local demo.
