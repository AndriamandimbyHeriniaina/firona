# Compose

One `docker-compose.yml`. One process per service. The browser talks **only** to nginx on the **host** port `NGINX_HOST_PORT` (default **8080**). Inside the container nginx still listens on 80.

| Service | Role | Published ports |
| --- | --- | --- |
| `db` | PostgreSQL 16 | 5432 (dev) |
| `redis` | Celery broker | 6379 (dev) |
| `backend` | Django | internal 8000 |
| `worker` | Celery worker | none |
| `beat` | Celery beat | none |
| `frontend` | Vite | internal 5173 |
| `nginx` | Gateway | **`${NGINX_HOST_PORT}:80`** (default 8080) |

Planned **v5** (not in compose yet): `llm` — Ollama, no published port, worker-only. See [product.md](product.md). When that service is added, also add `docs/llm.md` + skill + rule and link them in [INDEX.md](INDEX.md).

```bash
cp .env.example .env
docker compose up --build
```

Env: `.env` (never commit). Example: `.env.example`.

Prod later: same service names and routes; frontend becomes a built `dist`, nginx adds TLS.
