# Firona documentation index

Read this file first, then **only** the docs for the area you are changing.

| Field | Value |
| --- | --- |
| Current version | **v4 — Robustness** |
| Status | Collectors are idempotent per day, retried, budgeted and observable (`/api/v1/status/`). New Android-first UI (v3.5). Local LLM is v5. |
| Last updated | 2026-10-12 |

## Docs by function

| Function | Doc | Skill | Rule (when files match) |
| --- | --- | --- | --- |
| Product / non-goals | [product.md](product.md) | `firona-docs` | always (index only) |
| Legal sources | [sources.md](sources.md) | `firona-sources` | `sources.mdc` |
| Versions / roadmap | [versions.md](versions.md) | `firona-docs` | always (index only) |
| Compose orchestration | [compose.md](compose.md) | `firona-compose` | `compose.mdc` |
| Nginx gateway | [nginx.md](nginx.md) | `firona-nginx` | `nginx.mdc` |
| Django API | [backend.md](backend.md) | `firona-backend` | `backend.mdc` |
| Vue PWA | [frontend.md](frontend.md) | `firona-frontend` | `frontend.mdc` |
| Celery worker / beat | [workers.md](workers.md) | `firona-workers` | `workers.mdc` |
| PostgreSQL / Redis | [data.md](data.md) | `firona-data` | `data.mdc` |

## After shipping

Update **the function doc you touched** + [versions.md](versions.md) (status, decisions, date). Update `README.md` if ports or commands changed. Never rewrite past versions.
