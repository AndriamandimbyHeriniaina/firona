# Nginx gateway

Public HTTP entry. Config: `nginx/nginx.conf` (mounted on `nginx:1.27-alpine`).

| Path | Upstream |
| --- | --- |
| `/api/` | `backend:8000` |
| `/admin/` | `backend:8000` |
| `/static/` | `backend:8000` (dev; `collectstatic` later) |
| `/` | `frontend:5173` (Vite; WebSocket for HMR) |

Uses static `upstream` blocks (`backend:8000`, `frontend:5173`) resolved when nginx **starts**. Compose already waits for backend (healthy) and frontend (started). Do **not** use `resolver 127.0.0.11` (Docker/WSL often refuses UDP `:53`).

Host mapping: `${NGINX_HOST_PORT}:80` (default **8080**). Nginx inside the container still listens on 80. Use 80 on the host only when it is free (`NGINX_HOST_PORT=80`).

Django must see the original host: `Host`, `X-Forwarded-Proto`, `X-Forwarded-Host`.

## Production swap

Keep `/api` and `/admin`. Replace `/` with:

```nginx
root /usr/share/nginx/html;
try_files $uri $uri/ /index.html;
```

Mount Vue `dist`. Add TLS. Do not publish `backend` or `frontend` on the host.

## Leftover

TLS certificates; stop proxying `/static/` once `collectstatic` is in the image.
