# Backend (Django)

Project: `backend/` (`config/` + apps). DRF. Timezone `Indian/Antananarivo` (also the timezone of every `day` key).

## Apps

| App | Models | Role |
| --- | --- | --- |
| `catalog` | `Category`, `Product` | Articles, aliases, images, where-to-find, linked `Source`s |
| `sources` | `Source` | Legal gate (`can_collect`), collect health (`health`, `consecutive_failures`); Ads/Trends collectable, FB stored only |
| `trends` | `TrendSnapshot`, `CollectedSignal`, `CollectionRun` | Daily scores for now / past / future; raw legal-source hits; collector run log |

## HTTP

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/health/` | Liveness (no I/O) — Docker healthchecks |
| GET | `/api/health/ready/` | Database + cache; 503 when either is down |
| GET | `/api/v1/status/` | `ok` / `degraded` / `down` + checks (below) |
| GET | `/api/v1/products/` | |
| GET | `/api/v1/products/<slug>/` | Catalogue, 3-horizon radar, latest 15 days, sources with `health` / `last_success_at` |
| GET | `/api/v1/radar/?horizon=now\|past\|future` | |
| — | `/admin/` | |

Radar and detail responses carry an ETag and `Cache-Control: public, max-age=0, must-revalidate`: phones revalidate and get **304** when nothing changed (`ConditionalGetMiddleware`).

### `/api/v1/status/`

```json
{
  "status": "degraded",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "worker": {"ok": true, "last_heartbeat": "…", "age_seconds": 42},
    "queue": {"ok": true, "pending": 0},
    "data": {"ok": true, "latest_snapshot_at": "…", "age_hours": 0.4, "stale_after_hours": 13}
  },
  "sources": [{"name": "Google Trends MG", "kind": "google_trends", "health": "error", "consecutive_failures": 3, "…": "…"}],
  "failing_sources": ["Google Trends MG"]
}
```

`degraded` when: the cache is down, no worker heartbeat for `STATUS_HEARTBEAT_MAX_AGE_S` (15 min), more than `STATUS_QUEUE_WARN` queued tasks, newest snapshot older than `STATUS_STALE_HOURS` (13 h = two missed collects), or a collectable source's last run failed. `down` (HTTP 503) when the database is unreachable. Error text never appears here (admin only).

Behind nginx: `USE_X_FORWARDED_HOST`, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`.

```bash
docker compose exec backend python manage.py seed_demo --force
docker compose exec backend python manage.py collect_now
docker compose exec backend python manage.py test
```

First backend start: migrate + seed if `SEED_DEMO=1`. `seed_demo --force` overwrites the last 15 demo days in place (other days, including collected ones, are kept).

Collectors belong in Celery (see [workers.md](workers.md)), not in request/response. They must call `assert_can_collect` ([sources.md](sources.md)) before HTTP. Local LLM inference (v5) is the same rule: worker → Ollama, never Django views. Pipeline: [product.md](product.md).

`collect_now` without `META_ADS_ACCESS_TOKEN` skips Ads Library HTTP and leaves demo snapshots in place.

## Conventions

- Scores are keyed by local `day`; read "latest" with `order_by("-day", "-captured_at")` (`trends.services.LATEST_FIRST`), never by `captured_at` alone — recomputing a past day updates its `captured_at`.
- A test fails if models drift from migrations (`MigrationDriftTests`). Run `makemigrations` with every model change.
- Logs: `LOG_LEVEL` (default INFO); `httpx` / `httpcore` are pinned to WARNING because they print full URLs.
