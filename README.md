# Firona

Mobile-first web app that shows which **articles** are in demand on the Malagasy market: **now**, **past**, and **likely next**.

The product is a **demand radar**, not a map of physical markets. Signals will come from **legal, consented sources** (partner Facebook pages/groups, Meta Ads Library, Google Trends `MG`, later marketplace search logs). Scraping Facebook is out of scope.

Living product and architecture notes: [DOC.md](DOC.md).

## Stack (v1)

| Layer | Choice |
| --- | --- |
| Frontend | Vue 3 + Vite + PWA (later Capacitor → APK / iOS) |
| Backend | Django + Django REST Framework |
| Jobs | Celery worker + beat |
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
| http://localhost:5173 | Vue PWA (Passé / Maintenant / Futur) |
| http://localhost:8000/api/health/ | Backend liveness |
| http://localhost:8000/api/v1/radar/?horizon=now | Radar JSON (`now` \| `past` \| `future`) |
| http://localhost:8000/admin/ | Django admin |

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
| `frontend` | Vite dev server, proxies `/api` → `backend` |

## Repository layout

```
backend/     Django project (`config/`, apps: catalog, sources, trends)
frontend/    Vue 3 PWA
DOC.md       Versioned product + architecture log (evolves with the app)
README.md    How to run the current stack
```

## Conventions

- UI copy: French (Malagasy labels can be added later)
- Code comments, docstrings, this README, and `DOC.md`: English
- Chat with the team: French
- New features follow the **current version** in `DOC.md`. Do not skip versions unless asked.

## Troubleshooting

**`permission denied ... docker.sock`**

```bash
sudo usermod -aG docker $USER
newgrp docker
docker compose up --build
```

If `newgrp` is not enough, close the terminal, open a new one, retry.
