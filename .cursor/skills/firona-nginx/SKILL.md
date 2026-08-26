---
name: firona-nginx
description: >-
  Configures the Firona nginx gateway (routes, forwarded headers, prod swap).
  Use when editing nginx/, docker HTTP routing, port 80, reverse proxy, TLS,
  or how the browser reaches Vue and Django.
---

# Firona nginx

Read `docs/nginx.md` and `nginx/nginx.conf` before changing routing.

## Do

- Browser → nginx only. `/api` `/admin` `/static` → `backend:8000`. `/` → frontend (Vite in v1).
- Use static `upstream` + `proxy_pass http://django` (no `resolver 127.0.0.11`).
- Forward `Host`, `X-Forwarded-Proto`, `X-Forwarded-Host`.
- Vite HMR: WebSocket upgrade on `/`.

## Do not

- Publish Django or Vite on the host.
- Add a second public HTTP entry (another nginx in the frontend image for Compose).
- Scrape or proxy Facebook.

## After change

Patch `docs/nginx.md` and `README.md` URLs if the public port changes.
