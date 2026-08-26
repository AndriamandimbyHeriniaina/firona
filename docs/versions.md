# Versions

Source of truth for **what shipped** and **what is next**. Do not delete past versions: mark them done and append.

| Field | Value |
| --- | --- |
| Current version | **v2 — Legal source strategy** |
| Last updated | 2026-08-26 |

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
| **v3** | Collectors (Ads Library + Google Trends MG) on Celery | Planned |
| **v4** | Robustness: retries, idempotency, rate limits, observability | Planned |
| **v5** | Demand vs supply NLP (Malagasy / French) | Planned |
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

**Status:** Planned  
**Goal:** Celery jobs filling `TrendSnapshot` from Ads Library + Google Trends `MG`.

---

## v4 — Robustness of services

**Status:** Planned  
**Goal:** Retries, idempotent snapshots, timeouts, queue lag on health, rate-limit budgets.

---

## v5 — Language and demand vs supply

**Status:** Planned  
**Goal:** « mitady / cherche » vs « amidy / vente » in mixed Malagasy–French.

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
