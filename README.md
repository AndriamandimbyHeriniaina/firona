# Firona

Mobile-first web app that shows which **articles** are in demand on the Malagasy market: **now**, **past**, and **likely next**.

The product is a **demand radar**, not a map of physical markets. Signals will come from **legal, consented sources** (partner Facebook pages/groups, Meta Ads Library, Google Trends `MG`, later marketplace search logs). Scraping Facebook is out of scope.

Living docs (split by function): [docs/INDEX.md](docs/INDEX.md). Roadmap: [docs/versions.md](docs/versions.md).

## Stack (v1)

| Layer | Choice |
| --- | --- |
| Frontend | Vue 3 + Vite + PWA (later Capacitor → APK / iOS) |
| Backend | Django + Django REST Framework |
| Jobs | Celery worker + beat |
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
| http://localhost:8080/api/v1/radar/?horizon=now | Radar JSON (`now` \| `past` \| `future`) |
| http://localhost:8080/admin/ | Django admin |

The browser never talks to Vite or Django directly. Nginx routes `/` to the frontend and `/api`, `/admin`, `/static` to Django. Same layout in production (replace the Vite upstream with the built `dist`).

First boot runs migrations and `seed_demo` (sample products: rice, phones, generators, …).

```bash
docker compose exec backend python manage.py seed_demo --force
```

Stop: `Ctrl+C`, then `docker compose down`. Volumes keep Postgres data.

## Compose services

| Service | Role |
| --- | --- |
| `db` | PostgreSQL |
| `redis` | Celery broker / results |
| `backend` | Django API (`runserver` in dev) |
| `worker` | Celery worker (collectors later) |
| `beat` | Celery beat (schedules later) |
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

**Port 80 already in use**

Local default is **8080** (`NGINX_HOST_PORT` in `.env`) because 80 is often taken on WSL. Set `NGINX_HOST_PORT=80` only if that port is free. Keep `HMR_CLIENT_PORT` in sync (Compose does that from the same variable). Also set `CSRF_TRUSTED_ORIGINS` / `CORS_ALLOWED_ORIGINS` to `http://localhost:<port>`.
