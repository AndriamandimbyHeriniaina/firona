# Versions

Source of truth for **what shipped** and **what is next**. Do not delete past versions: mark them done and append.

| Field | Value |
| --- | --- |
| Current version | **v4 — Robustness** |
| Last updated | 2026-10-12 |

## How to update

1. Set **Current version** and **Last updated** here and in [INDEX.md](INDEX.md).
2. In that version: Planned → In progress → Done.
3. Record **Decisions** (why) and **Follow-ups**.
4. Patch the matching **function** doc (`nginx.md`, `backend.md`, …).
5. Patch `README.md` if setup changed.

Stay on the current version unless the user starts the next one.

## Roadmap

| Version | Theme | Status |
| --- | --- | --- |
| **v1** | Init: Docker, Django, Vue PWA, nginx gateway, demo radar | **Done** |
| **v2** | Legal source strategy (no scraping) | **Done** |
| **v3** | Collectors (Ads Library + Google Trends MG) on Celery | **Done** |
| **v3.5** | Interface refresh (motion, Android) + v1–v3 audit fixes | **Done** |
| **v4** | Robustness: retries, idempotency, rate limits, observability | **Done** |
| **v5** | Local LLM (Ollama) + demand vs supply NLP | Planned |
| **v6** | Product UX: history, categories, regions | Planned |
| **v7** | PWA harden + Capacitor | Planned |
| **v8** | Partner marketplace search logs | Planned |

---

## v1 — Initialization

**Status:** Done  
**Goal:** Runnable webapp to iterate on radar UI/API without real social data.

### Shipped

- Monorepo `backend/` + `frontend/` + `nginx/`
- Compose: `db`, `redis`, `backend`, `worker`, `beat`, `frontend`, `nginx`
- Nginx only public HTTP (host port `NGINX_HOST_PORT`, default 8080; container still :80)
- Apps: `catalog`, `sources`, `trends`
- Demo seed + mobile UI Passé / Maintenant / Futur
- Article **detail** page (images, description, where to find, linked sources, 3-horizon scores)
- Celery wired (heartbeat only)

### Out of scope

- Scraping, real collectors, TLS, Capacitor, auth

### Decisions

- Webapp first, APK later
- Collectors stay server-side
- Nginx gateway now; prod = same routes, swap Vite for `dist` + TLS
- Scores stored by us; demo data until v3

### Follow-ups

- v2: source policy checklist, partner page/group types
- Infra leftover: TLS, `collectstatic` instead of proxying `/static/`

---

## v2 — Legal source strategy

**Status:** Done  
**Goal:** Enforceable source matrix so collectors cannot scrape Facebook.

### Shipped

- Policy doc: `docs/sources.md`
- `Source` gate: `can_collect` / `block_reason` / `revoke_consent` / last success-error
- Collectable kinds for the next slice: `meta_ads`, `google_trends` only
- Facebook pages/groups and marketplace partners: stored, **not** fetched until a later version
- Celery `audit_sources` (no outbound HTTP)
- Django tests on the gate

### Out of scope (on purpose)

- HTTP collectors (v3)
- NLP (v5)

### Decisions

- One function `assert_can_collect` before any future HTTP
- Revoking consent stops collects but **keeps** historical snapshots
- “Everywhere” is not a source kind

### Follow-ups for v3

- Celery beat: Ads Library + Google Trends `MG` behind the gate
- `mark_success` / `mark_error` from those jobs

---

## v3 — First collectors

**Status:** Done  
**Goal:** Celery jobs filling `TrendSnapshot` from Ads Library + Google Trends `MG`.

### Shipped

- Beat: `collect_legal_sources` every 6 hours (`apps.trends.tasks.collect_legal_sources`)
- Manual run: `python manage.py collect_now`
- `assert_can_collect` inside `gated_request` (no HTTP if denied)
- geo / `ad_reached_countries` locked to **MG**
- `CollectedSignal` (public ad ids, trend titles) then scores on **existing** `Product` rows
- `mark_success` / `mark_error` on each source
- Missing `META_ADS_ACCESS_TOKEN` or Trends RSS HTTP 400: log, do **not** overwrite demo snapshots
- Tests: Facebook / inactive / geo≠MG never open a socket

### Out of scope

- Local LLM / Ollama (v5)
- Auto-creating articles from raw ads or queries
- Facebook page/group fetch even with consent
- Retries, rate-limit budgets, queue lag on health (v4)

### Decisions

- Collect is a Celery engine, not Django views
- Raw fetch and later AI organise stay different jobs
- Demo seed remains until collectors produce real scores
- Google has **no public daily RSS for `geo=MG`** today (HTTP 400). The collector still calls that official feed only; it does not scrape Trends HTML or fall back to another country
- Ads Library for MG returns **political / issue ads only** (Meta: commercial archive is EU/UK). Empty commercial hits do not zero-out supply scores
- Store public ad ids and trend titles, never creative bodies or phones

### Follow-ups

- Official Google Trends API alpha (`trends.googleapis.com`) when a project is allow-listed
- v4: retries, idempotent daily snapshots, timeouts/budgets as first-class health
- v5: local LLM on `CollectedSignal` text
---

## v3.5 — Interface refresh & audit

**Status:** Done (2026-10-12)
**Goal:** A stylish, animated, Android-first PWA, and a pass over v1–v3 before adding robustness.

Not a roadmap slice of its own: requested between v3 and v4. No v6 features (history screens, category filters, regions) were pulled forward.

### Shipped (UI)

- Design system in `frontend/src/styles.css`: dark + light themes (system setting), one accent per horizon (Passé gold, Maintenant red, Futur cyan), Plus Jakarta Sans (self-hosted, latin subset precached)
- Animated radar (`RadarScope.vue`): rotating sweep, blips pulse when the beam passes, fixed bearing per article, tap to open
- Cards with score ring, demand/supply bars, momentum; detail screen with 3-horizon rings, demand-vs-supply verdict, interactive history chart (finger scrub), sources with collect health, native share
- View Transitions (Chrome / Android WebView 111+): thumbnail → hero morph, directional slides between horizons, nav bar slides away on articles
- Touch: swipe between horizons, pull-to-refresh, ripples, haptic ticks, 44–48 px targets, safe areas
- Speed: stale-while-revalidate store (instant tab switches), other horizons prefetched, lazy detail chunk, skeletons, `lite` mode on ≤ 2 GB RAM / Data Saver (no blur, no glow), `prefers-reduced-motion` honoured
- PWA: PNG icons (192/512/maskable), Android shortcuts (long-press), offline API cache (NetworkFirst, 5 s timeout), install button, offline banner
- New article illustrations (valid UTF-8 SVG, no baked-in text)

### Audit fixes (v1–v3)

| Version | Problem | Fix |
| --- | --- | --- |
| v1 | Article history returned the 15 **oldest** snapshots | Latest 15 days, oldest → newest |
| v1 | Detail rebuilt the whole radar 3× to find one article | `product_radar()` (one query) |
| v1 | Demo seed drew falling curves for positive momentum | Demand climbs to today's value |
| v1 | `groupe.svg` / `riz-marche.svg` were Latin-1 (broken image) | Redrawn as UTF-8 |
| v1 | Prod frontend image had no SPA fallback (deep links 404) | `frontend/nginx/spa.conf` |
| v1 | nginx kept a dead backend IP after the backend container was recreated (502) | Compose `depends_on.restart: true` |
| v3 | Migrations had drifted from models (index names, help_text) | Migrations fixed + drift test |
| v3 | Substring matching (`riz` in `prize`), no accent folding | Whole words, accent-insensitive, longest term wins |
| v3 | `refresh_radar_snapshots` never matched a signal (exact timestamp) | Works per local day |
| v3 | `httpx` logged the Ads token (query string) at INFO | `httpx` → WARNING + redaction everywhere |
| v3 | Worker image lacked `httpx` (installed by hand in the old container) | Images rebuilt from `requirements.txt` |

---

## v4 — Robustness of services

**Status:** Done (2026-10-12)
**Goal:** Retries, idempotent snapshots, timeouts, queue lag on health, rate-limit budgets.

Collectors stay reliable before we add a model. No LLM in this slice.

### Shipped

- **Idempotent days:** `TrendSnapshot` and `CollectedSignal` carry `day` (local date, Antananarivo) with unique keys. Re-running a collector updates today's rows; momentum compares with the previous **day**, not the previous run
- **HTTP:** pooled client per run, split timeouts, 3 attempts with exponential backoff + full jitter on timeouts / 429 / 5xx, `Retry-After` honoured (≤ 60 s), 4xx not retried
- **Legal gate on every attempt:** consent revoked or source disabled between two attempts stops the next request
- **Budgets:** hourly request budget per source kind in the cache (`COLLECT_BUDGET_*`), checked before the socket opens
- **Celery:** single-flight lock (beat, manual `collect_now`, retries never overlap), soft/hard time limits, auto-retry on DB blips, `acks_late`, prefetch 1, beat entries expire instead of piling up
- **Observability:** `CollectionRun` log per collector × source (requests, retries, signals, duration, redacted detail) in the admin; `Source.health` / `consecutive_failures`; worker heartbeat every 5 min; `/api/health/ready/`; `/api/v1/status/` (`ok` / `degraded` / `down`: worker, queue backlog, data freshness, failing sources); worker Docker healthcheck
- **API:** ETag + `must-revalidate` (304 on unchanged radar), nginx gzip
- 50 backend tests (was 14), including a migration drift guard
- Independent review pass fixed: soft time limit no longer swallowed, gate re-read before every request (not only retries), log redaction filter + no redirects with the token, HTTP-date `Retry-After`, race-safe upserts, body timeout and pull-to-refresh error toast in the PWA, Chrome < 111 colour support (no `color-mix()`), per-navigation view-transition hand-off

### Decisions

- Meta token stays in the query string (the officially documented form); it is kept out of logs and stored errors instead of moving to a header we could not verify against Meta's docs
- Public status shows health, never error text (error text stays in the admin)
- Ads value = distinct public ad ids seen that day (union across runs)
- nginx keeps static upstreams (no `resolver`, see nginx.md); Compose restarts it with the backend

### Follow-ups

- v5: local LLM on `CollectedSignal` titles
- Alerting on `/api/v1/status/` (an external uptime monitor is enough)
- Official Google Trends API alpha when allow-listed (RSS `geo=MG` still returns 400)

---

## v5 — Language and demand vs supply

**Status:** Planned  
**Goal:** Filter and organise collected text: « mitady / cherche » vs « amidy / vente » in mixed Malagasy–French, locally and for free.

### Planned

- Compose service `llm` (Ollama), internal only, volume for models
- Worker calls `http://llm:11434` — never from Django, never from the browser
- Default instruct model: `qwen3.5:4b` (Q4). Fallback: `gemma3:4b`
- Lexicon pass first; LLM only when the text is ambiguous
- Optional later: embeddings in the same Ollama (`nomic-embed-text`) to group aliases

### Out of scope

- Cloud LLM APIs as the organiser
- Large GPU-only stacks (vLLM, 70B)
- Fetching new source kinds (still Ads Library + Trends until a later version)

### Decisions

- Speed is not a goal: CPU batch jobs are enough
- GPU on WSL is optional
- A dedicated `docs/llm.md` + skill lands when the Compose service is added

---

## v6 — Product UX

**Status:** Planned  
**Goal:** History charts, category filters, Tana vs regions.

---

## v7 — Installable app

**Status:** Planned  
**Goal:** Offline PWA shell + Capacitor Android.

---

## v8 — Marketplace partners

**Status:** Planned  
**Goal:** Ingest search logs. Partnership-first.
