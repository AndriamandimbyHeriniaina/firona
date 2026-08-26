---
name: firona-frontend
description: >-
  Implements the Firona Vue 3 PWA (radar UI, Vite, HMR behind nginx).
  Use when editing frontend/, Vue components, Vite config, PWA, or the
  Passé / Maintenant / Futur screens.
---

# Firona frontend

Read `docs/frontend.md` before editing Vue.

## Do

- `fetch('/api/...')` only (relative). Nginx same-origin.
- UI in French. `HMR_CLIENT_PORT` must match the public nginx port in Compose.
- Keep the three horizons as routes `/past` `/now` `/future`.
- Article detail: `/article/:slug` (query `from` = horizon). Relative API `GET /api/v1/products/:slug/`.

## Do not

- Vite `server.proxy` to Django.
- Hardcode `localhost:8000` or `localhost:5173` for API calls.
- Add Capacitor until versions.md v7.

## After change

Patch `docs/frontend.md`.
