# Frontend (Vue)

Vue 3 + Vite + PWA in `frontend/`. Mobile-first. UI copy: French.

The app calls **relative** URLs (`/api/v1/radar/?horizon=…`, `/api/v1/products/<slug>/`). Nginx makes that same-origin. Do not point the browser at Vite or Django ports.

Routes: `/now` `/past` `/future` (list) and `/article/:slug` (detail, query `from` to return to the same horizon). Cards show a thumbnail; the detail screen has gallery, description, where to find, data sources (collectable vs blocked), three-horizon scores, and a 15-day sparkline.

## Dev behind nginx

Compose sets `HMR_CLIENT_PORT` from `NGINX_HOST_PORT` (default 8080) so the HMR websocket uses the public host port, not 5173.

Local `npm run dev` without Docker: leave `HMR_CLIENT_PORT` unset (HMR on 5173).

No Vite `/api` proxy — that would bypass the gateway.

## Later

Capacitor wraps this PWA (versions.md v7). Do not add a native shell in v1.
