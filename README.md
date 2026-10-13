# Firona

Mobile-first web app that shows which **articles** are in demand on the Malagasy market: **now**, **past**, and **likely next**.

The product is a **demand radar**, not a map of physical markets. Signals will come from **legal, consented sources** (partner Facebook pages/groups, Meta Ads Library, Google Trends `MG`, later marketplace search logs). Scraping Facebook is out of scope.

Living docs (split by function): [docs/INDEX.md](docs/INDEX.md). Sources policy: [docs/sources.md](docs/sources.md). Product pipeline (API / collect / local LLM): [docs/product.md](docs/product.md). Roadmap: [docs/versions.md](docs/versions.md) (**current: v4** robustness; next: **v5** Ollama).

## Stack (v4)

| Layer | Choice |
| --- | --- |
| Frontend | Vue 3 + Vite + PWA, Android-first (view transitions, gestures, offline cache; later Capacitor → APK / iOS) |
| Backend | Django + Django REST Framework |
| Jobs | Celery worker + beat (collect every 6h with retries, budgets and a lock; heartbeat; daily prune) |
| Gateway | Nginx (host `NGINX_HOST_PORT`, default 8080) |
| Data | PostgreSQL 16, Redis 7 |
| Run | One `docker-compose.yml`, one process per service |

## Prerequisites

- Docker Engine + Docker Compose v2
- Your Unix user in the `docker` group (see [Troubleshooting](#troubleshooting))
- Copy env: `cp .env.example .env`

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

| URL | What |
| --- | --- |
| http://localhost:8080 | Vue PWA (Passé / Maintenant / Futur) |
| http://localhost:8080/api/health/ | Backend liveness |
| http://localhost:8080/api/v1/status/ | Service state: worker, queue, data freshness, sources |
| http://localhost:8080/api/v1/radar/?horizon=now | Radar JSON (`now` \| `past` \| `future`) |
| http://localhost:8080/api/v1/products/telephone/ | Article detail JSON |
| http://localhost:8080/admin/ | Django admin |

The browser never talks to Vite or Django directly. Nginx routes `/` to the frontend and `/api`, `/admin`, `/static` to Django. Same layout in production (replace the Vite upstream with the built `dist`).

First boot runs migrations and `seed_demo`. After pulling model changes:

```bash
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py seed_demo
```

Tap an article on the radar to open its detail (images, where to find, sources). Recreate demo scores with `--force`. Run collectors without wiping the catalogue:

```bash
docker compose exec backend python manage.py seed_demo --force
docker compose exec backend python manage.py collect_now
```

Stop: `Ctrl+C`, then `docker compose down`. Volumes keep Postgres data.

Optional: set `META_ADS_ACCESS_TOKEN` in `.env` for the official Ads Library API. Google Trends uses the public RSS `geo=MG` (no key); if Google returns 400, demo scores stay and `/api/v1/status/` reports `degraded`.

Tests:

```bash
docker compose exec backend python manage.py test
docker compose exec frontend npx vue-tsc --noEmit
```

On an Android phone on the same network, open `http://<PC-IP>:8080` in Chrome, then **Installer l'application** (button in the top bar) for the home-screen app with shortcuts.

## Compose services

| Service | Role |
| --- | --- |
| `db` | PostgreSQL |
| `redis` | Celery broker / results |
| `backend` | Django API (`runserver` in dev) |
| `worker` | Celery worker (Ads Library + Trends MG collectors), Docker healthcheck |
| `beat` | Celery beat (collect every 6h, heartbeat 5 min, prune daily) |
| `frontend` | Vite dev server (internal only) |
| `nginx` | Public HTTP gateway (`NGINX_HOST_PORT`, default **8080**) |

## Repository layout

```
backend/     Django project (`config/`, apps: catalog, sources, trends)
frontend/    Vue 3 PWA
nginx/       Reverse-proxy config (the production-shaped gateway)
docs/        Function docs (INDEX, versions, nginx, backend, …)
README.md    How to run the current stack
```

## Conventions

- UI copy: French (Malagasy labels can be added later)
- Code comments, docstrings, README, and `docs/`: English
- Chat with the team: French
- New features follow the **current version** in `docs/versions.md`. Do not skip versions unless asked.

## Troubleshooting

**`permission denied ... docker.sock`**

```bash
sudo usermod -aG docker $USER
newgrp docker
docker compose up --build
```

If `newgrp` is not enough, close the terminal, open a new one, retry.

**502 from `/api` after recreating only the backend**

Nginx resolved the old container IP at start: `docker compose restart nginx`. A full `docker compose up -d` restarts it for you.

**`ModuleNotFoundError` in `worker` / `beat` after pulling**

The three Python services share one image: `docker compose build backend worker beat && docker compose up -d`.

**Port 80 already in use**

Local default is **8080** (`NGINX_HOST_PORT` in `.env`) because 80 is often taken on WSL. Set `NGINX_HOST_PORT=80` only if that port is free. Keep `HMR_CLIENT_PORT` in sync (Compose does that from the same variable). Also set `CSRF_TRUSTED_ORIGINS` / `CORS_ALLOWED_ORIGINS` to `http://localhost:<port>`.
