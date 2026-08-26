# Workers (Celery)

Services `worker` and `beat` share the backend image.

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Broker / results: `REDIS_URL` (see [data.md](data.md)).

v2: `ping_stack` + `audit_sources` (classifies sources, **no HTTP**). `CELERY_BEAT_SCHEDULE` stays empty until v3 collectors.

Every collector must call `assert_can_collect(source)` first. See [sources.md](sources.md). Revoked consent stops new fetches; snapshots stay.
