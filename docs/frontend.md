# Frontend (Vue)

Vue 3 + Vite + PWA in `frontend/`. Mobile-first, tuned for Android Chrome. UI copy: French.

The app calls **relative** URLs (`/api/v1/radar/?horizon=…`, `/api/v1/products/<slug>/`). Nginx makes that same-origin. Do not point the browser at Vite or Django ports.

## Screens

| Route | Screen |
| --- | --- |
| `/past` `/now` `/future` | Radar: animated scope (`RadarScope.vue`) + ranked cards (`TrendCard.vue`) |
| `/article/:slug?from=<horizon>` | Detail: hero carousel, 3-horizon rings, demand vs supply verdict, history chart, where to find, sources (collect health), share |

Unknown paths redirect to `/now`.

## Layout of `src/`

| Path | Role |
| --- | --- |
| `styles.css` | Design tokens (dark + light), primitives (`.surface`, `.pill`, `.btn`, `.icon-btn`, `.skeleton`, `.rise`), view-transition keyframes, `lite` + reduced-motion overrides |
| `api.ts` | Types, French labels, `fetch` with timeout and French `ApiError` messages |
| `stores/radar.ts` | Pinia stale-while-revalidate cache (per horizon, per article), request de-dupe, prefetch |
| `lib/viewTransition.ts` | Router ↔ View Transitions API (direction in `html[data-vt]`) |
| `lib/device.ts` | `prefersReducedMotion`, `isLiteDevice`, `haptic` |
| `lib/format.ts` | French relative time, dates, signed numbers |
| `composables/` | `useTouchGestures` (swipe + pull-to-refresh), `useCountUp`, `useApp` (install prompt, online state, toasts) |
| `directives/` | `v-ripple`, `v-reveal` (adds `.is-in` when visible) |

## Design rules

- Colors only through tokens. Each horizon sets `--accent` / `--accent-rgb` via `[data-horizon]`: Passé gold, Maintenant red, Futur cyan. Trend labels set `--tone` / `--tone-rgb` via `[data-label]`.
- Tints: `rgb(var(--accent-rgb) / 0.16)`, never `color-mix()` (Chrome 111+ only; many Android phones in Madagascar run older Chrome). `100dvh` always follows a `100vh` fallback.
- Animate **transform / opacity** only (bars use `scaleX`, shimmer translates). No layout animation.
- Every animation must degrade: `prefers-reduced-motion` disables them; `html.lite` (≤ 2 GB RAM, ≤ 2 cores, or Data Saver) drops backdrop blur and the aura glow.
- Data that is already cached renders **still** (`animate=false`): no replayed count-ups when coming back from an article; this also keeps view-transition snapshots clean.
- Touch targets ≥ 44 px; the radar page has `touch-action: pan-y` so vertical scroll stays native and horizontal drags feed the swipe.
- `html { overscroll-behavior-y: none }`: our pull-to-refresh replaces Chrome's (which would reload the PWA).

## Motion

- View Transitions (Chrome / WebView 111+): named groups `page`, `appbar`, `topbar`, `nav`, `scope`, `blip-<slug>`, `hero`. The tapped card's thumbnail gets `hero` (store `activeSlug`) and morphs into the detail carousel.
- Without the API, a CSS `<Transition name="route">` is used instead. Never wrap the router view in a CSS-less out-in `<Transition>`: its leave finishes synchronously and crashes the RouterView.

## PWA

`vite.config.ts`: PNG icons (`public/icons/`, maskable included), Android shortcuts, `start_url: /now`. Workbox precaches JS/CSS/HTML/SVG + the latin font (~240 KB), not the install icons. `/api/v1/*` uses NetworkFirst (5 s timeout) so the last radar opens offline. Regenerate icons from `public/favicon.svg` if the brand changes.

## Dev behind nginx

Compose sets `HMR_CLIENT_PORT` from `NGINX_HOST_PORT` (default 8080) so the HMR websocket uses the public host port, not 5173.

Local `npm run dev` without Docker: leave `HMR_CLIENT_PORT` unset (HMR on 5173).

No Vite `/api` proxy — that would bypass the gateway.

Production image (`Dockerfile` target `prod`) serves `dist` with `nginx/spa.conf`: immutable hashed assets, revalidated `sw.js` / `index.html`, SPA fallback for deep links.

## Later

Capacitor wraps this PWA (versions.md v7). Do not add a native shell before that.
