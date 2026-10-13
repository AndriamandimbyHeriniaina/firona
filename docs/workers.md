# Workers (Celery)

Services `worker` and `beat` share the backend image. Rebuild them when `requirements.txt` changes (`docker compose build backend worker beat`): a package installed by hand in a container disappears when Compose recreates it.

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Broker / results: `REDIS_URL` (DB 0). Locks, budgets and heartbeat: Django cache (`REDIS_CACHE_URL`, DB 1). See [data.md](data.md).

## Schedule

| Beat entry | Task | Every | Expires if not picked up |
| --- | --- | --- | --- |
| `collect-legal-sources` | `apps.trends.tasks.collect_legal_sources` | 6 h | 3 h |
| `worker-heartbeat` | `apps.trends.tasks.heartbeat` | 5 min | 4 min |
| `prune-collection-runs` | `apps.trends.tasks.prune_collection_runs` | daily 03:30 | 6 h |

Manual (same lock as beat, never overlaps it):

```bash
docker compose exec backend python manage.py collect_now
```

## Collect flow

`assert_can_collect` → `gated_request` (retries, budget) → `CollectedSignal` (upsert per day) → `TrendSnapshot` (upsert per day) for **matched existing products only**. Unmatched trend titles are counted, never inserted as articles. Each collector × source pass writes a `CollectionRun`.

| Task | HTTP | Notes |
| --- | --- | --- |
| `audit_sources` | no | Classify the gate |
| `collect_google_trends` | `https://trends.google.com/trending/rss?geo=MG` | Public RSS; MG currently returns HTTP 400 (not retried: 4xx) |
| `collect_meta_ads` | Graph `ads_archive` | Needs `META_ADS_ACCESS_TOKEN`; country `MG` |
| `collect_legal_sources` | both, then scores | Beat entry |
| `refresh_radar_snapshots` | no | Recompute today's scores from stored signals |
| `heartbeat` | no | Writes `firona:heartbeat:worker` for `/api/v1/status/` |
| `prune_collection_runs` | no | Closes orphaned `running` rows, deletes runs older than `COLLECT_RUN_RETENTION_DAYS` |

## Robustness (v4)

| Concern | Behaviour | Setting |
| --- | --- | --- |
| Idempotency | One signal per source × product × metric × day; one snapshot per product × window × day. Trends keeps the best rank of the day; Ads keeps the union of public ad ids | — |
| Momentum | Today's demand − previous **day's** demand | — |
| Timeouts | connect ≤ 6 s, read `COLLECT_HTTP_TIMEOUT` | `COLLECT_HTTP_TIMEOUT=20` |
| Retries | Timeouts, connection errors, 429, 500/502/503/504; exponential backoff with full jitter; `Retry-After` (seconds or HTTP date) honoured, and a wait over 60 s stops the run instead of hammering; other 4xx returned at once | `COLLECT_HTTP_ATTEMPTS=3`, `COLLECT_RETRY_BASE_S`, `COLLECT_RETRY_CAP_S` |
| Legal gate | Re-read from the DB before **every** request: a revoke in the admin stops the next call, even mid-run | — |
| Rate limits | Hourly request budget per source, counted in the cache before the socket opens | `COLLECT_BUDGET_META_ADS=150`, `COLLECT_BUDGET_GOOGLE_TRENDS=20` |
| Overlap | Cache lock `firona:lock:collect`; a second run returns `{"skipped": …}` | — |
| Runaway | Soft limit closes the run as `error` and stops the task; hard kill 2 min later | `COLLECT_SOFT_TIME_LIMIT=900` |
| Races | Daily upserts use `get_or_create` + row lock, so two overlapping runs never fail on the unique key | — |
| Lost worker | `acks_late` + `reject_on_worker_lost`: the task goes back to the queue | — |
| DB blips | Task auto-retry (backoff 30 s → 10 min, jitter, 3 times) | — |
| Secrets | `httpx` logs at WARNING; a logging filter redacts every message and traceback; stored errors are redacted; requests carrying the Ads token never follow redirects | — |

If a source is denied, inactive, geo≠MG, over budget, or the Ads token is empty: **no HTTP**. `mark_error` sets `last_error_at` and `consecutive_failures`; existing radar snapshots stay.

## Observability

- Admin → **Collection runs**: requests, retries, signals, duration, redacted detail per pass
- Admin → **Sources**: health, consecutive failures, last success / error
- `GET /api/v1/status/`: see [backend.md](backend.md)
- `worker` has a Docker healthcheck (`celery inspect ping`)

Facebook pages/groups are never fetched. Inference (Ollama) is v5, never in Django views.

See [sources.md](sources.md) and [product.md](product.md).
