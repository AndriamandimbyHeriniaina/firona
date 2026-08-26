# Workers (Celery)

Services `worker` and `beat` share the backend image.

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Broker / results: `REDIS_URL` (see [data.md](data.md)).

v1: `ping_stack` heartbeat only. `CELERY_BEAT_SCHEDULE` is empty until v3 collectors.

Do not scrape Facebook from tasks. A task may run only if the `Source` is `is_active` and `consent_granted` (when the kind requires consent).
