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
- Colors from tokens in `styles.css`; horizon accent via `[data-horizon]`, trend tone via `[data-label]`. Dark + light.
- Data through `useRadarStore` (stale-while-revalidate), not raw `fetch` in views.
- Animate transform/opacity only; respect `prefers-reduced-motion` and `html.lite`; cached data renders with `animate=false`.
- Touch targets ≥ 44 px. Use `v-ripple` on tappable surfaces, `haptic()` for discrete actions.

## Do not

- Vite `server.proxy` to Django.
- Hardcode `localhost:8000` or `localhost:5173` for API calls.
- Add Capacitor until versions.md v7.
- Wrap `<router-view>` in a CSS-less out-in `<Transition>` (crashes the RouterView; view transitions handle it).
- Animate `width`/`height`/`top` or add a heavy blur outside `.glass-bar` (low-end Android).

## After change

Patch `docs/frontend.md`.
