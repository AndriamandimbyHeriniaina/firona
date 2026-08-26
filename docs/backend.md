# Backend (Django)

Project: `backend/` (`config/` + apps). DRF. Timezone `Indian/Antananarivo`.

## Apps

| App | Models | Role |
| --- | --- | --- |
| `catalog` | `Category`, `Product` | Articles + aliases (`findy`, `vary`) |
| `sources` | `Source` | Legal sources only; `consent_granted` required for FB |
| `trends` | `TrendSnapshot` | Scores for now / past / future |

## HTTP

| Method | Path |
| --- | --- |
| GET | `/api/health/` |
| GET | `/api/v1/products/` |
| GET | `/api/v1/radar/?horizon=now\|past\|future` |
| — | `/admin/` |

Behind nginx: `USE_X_FORWARDED_HOST`, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`.

```bash
docker compose exec backend python manage.py seed_demo --force
```

First backend start: migrate + seed if `SEED_DEMO=1`.

Collectors belong in Celery (see [workers.md](workers.md)), not in request/response.
