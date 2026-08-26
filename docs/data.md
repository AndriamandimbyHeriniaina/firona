# Data stores

| Service | Image | Role | Compose port |
| --- | --- | --- | --- |
| `db` | postgres:16-alpine | Django database | 5432 (dev only) |
| `redis` | redis:7-alpine | Celery broker + result backend | 6379 (dev only) |

Django reads `POSTGRES_*`. Celery reads `REDIS_URL` (default `redis://redis:6379/0`).

Volume `postgres_data` survives `docker compose down`.

Do not put secrets in git. Change `POSTGRES_PASSWORD` outside local demo.
