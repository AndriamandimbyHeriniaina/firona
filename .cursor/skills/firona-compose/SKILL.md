---
name: firona-compose
description: >-
  Wires Firona Docker Compose services (depends_on, healthchecks, ports).
  Use when editing docker-compose.yml, adding a service, or changing how
  containers start together.
---

# Firona compose

Read `docs/compose.md` before editing `docker-compose.yml`.

## Do

- Keep **one** compose file, **one process per service**.
- HTTP publish: `${NGINX_HOST_PORT}:80` (default 8080). `expose` backend 8000 and frontend 5173 internally.
- Keep `HMR_CLIENT_PORT` equal to `NGINX_HOST_PORT`.
- Health: db/redis/backend; nginx depends on backend healthy + frontend started.

## Do not

- Merge frontend+nginx or backend+worker into one service.
- Add a new public port without updating `README.md` and `docs/nginx.md`.

If you add a **new** Compose service, add `docs/<name>.md`, `.cursor/skills/firona-<name>/`, and `.cursor/rules/<name>.mdc`, then link them in `docs/INDEX.md`.

## After change

Patch `docs/compose.md` and `README.md`.
