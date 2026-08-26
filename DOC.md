# Firona — living documentation

This file is the **source of truth** for what we already shipped, what we are building now, and what comes next. It grows with the project. Do not delete past versions: mark them done and append.

| Field | Value |
| --- | --- |
| Current version | **v1 — Initialization** |
| Status | Done (scaffold). Collectors are not implemented. |
| Last updated | 2026-08-26 |

## How to update this file

When a version (or a slice of a version) ships:

1. Set **Current version** and **Last updated**.
2. Move the work from Planned → In progress → Done in that version’s section.
3. Record **Decisions** (why, not only what) and **Follow-ups**.
4. If install / ports / commands change, update `README.md` in the same change.

Agents must read `README.md` and this file **before** coding, and patch this file **after** shipping.

---

## Roadmap (high level)

| Version | Theme | Status |
| --- | --- | --- |
| **v1** | Project initialization: Docker, Django, Vue PWA, domain models, demo radar | **Done** |
| **v2** | Legal source strategy and contracts (no scraping) | Planned |
| **v3** | First collectors (Ads Library + Google Trends MG) on Celery | Planned |
| **v4** | Robustness: retries, idempotency, rate limits, observability | Planned |
| **v5** | Demand vs supply NLP (Malagasy / French / mixed) | Planned |
| **v6** | Product UX: history, categories, regions | Planned |
| **v7** | Package as installable app (PWA harden + Capacitor) | Planned |
| **v8** | Partner marketplaces (search logs) | Planned |

Details live in the sections below. Later versions stay thin until we start them.

---

## v1 — Initialization

**Status:** Done  
**Goal:** A runnable webapp so we can iterate on the radar UI and API without real social data yet.

### In scope (shipped)

- Monorepo with `backend/` (Django 5.2 + DRF) and `frontend/` (Vue 3 + Vite + PWA)
- Single `docker-compose.yml`: `db`, `redis`, `backend`, `worker`, `beat`, `frontend`
- Domain apps:
  - `catalog` — `Category`, `Product` (+ aliases such as `findy`, `vary`)
  - `sources` — consented / public APIs only (`consent_granted` flag)
  - `trends` — `TrendSnapshot` scores for now / past / future
- API: `GET /api/health/`, `GET /api/v1/products/`, `GET /api/v1/radar/?horizon=`
- Demo seed so the three horizons are not empty
- Mobile-first UI: Passé / Maintenant / Futur
- Celery app wired (heartbeat task only)

### Out of scope (on purpose)

- Any Facebook / Marketplace / group scraping
- Real collectors, Meta tokens, production Nginx
- Capacitor native shells
- Auth / multi-tenant

### Decisions

- **Webapp first**, APK later: PWA now, Capacitor when the radar is useful.
- **Vue + Django**, not a SPA calling third parties from the browser: collectors stay server-side.
- **Radar.com maps** are not the product. Location filters can wait.
- **Scores are stored by us.** No vendor will give three years of Malagasy Marketplace history.
- Demo data is allowed until v3; the UI must not pretend it is live Facebook.

### Follow-ups for v2

- Write the source policy (allowed vs forbidden) as an implementation checklist
- List first partner page/group types and Ads Library query shape

---

## v2 — Legal source strategy

**Status:** Planned  
**Goal:** A written, enforceable strategy so collectors cannot “just scrape Facebook”.

### In scope (when we start)

- Source matrix: Ads Library, Google Trends `geo=MG`, opt-in Pages, admin-consented public groups, later marketplace APIs
- What we store vs what we never store (PII, Messenger, private groups)
- `Source` records as the only switch collectors may use (`is_active` + `consent_granted`)
- Failure mode if a source is revoked

### Out of scope

- Implementing HTTP collectors (v3)
- NLP (v5)

### Open questions

- Who owns partner outreach (group admins)?
- Ads Library coverage for commercial ads in Madagascar (not only political)

### Decisions

_(fill when the version starts)_

---

## v3 — First collectors

**Status:** Planned  
**Goal:** Periodic jobs that fill `TrendSnapshot` from **two** legal sources so the radar is no longer demo-only.

### In scope (when we start)

- Celery tasks + beat schedules
- Meta Ads Library client (public API)
- Google Trends `MG` client
- Map raw counts → `demand_score` / `supply_score` / `momentum` / `emerging_score`
- Admin-visible last success / last error per `Source`

### Out of scope

- Facebook Graph on pages we do not manage
- Marketplace listings without Content Library / partner API
- Full robustness platform (v4)

### Decisions

_(fill when the version starts)_

---

## v4 — Robustness of services

**Status:** Planned  
**Goal:** Collectors and API stay correct when Meta/Google fail, rate-limit, or return garbage.

### In scope (when we start)

- Retry with backoff, dead-letter / error log, idempotent snapshots (one row per product per window)
- Timeouts, circuit breaker around external HTTP
- Structured logs + health that includes queue lag
- Rate-limit respect and budget per source
- Contract tests / fixtures for parser changes

### Out of scope

- Kubernetes, multi-region
- Paid social-listening SaaS unless we explicitly choose one

### Decisions

_(fill when the version starts)_

---

## v5 — Language and demand vs supply

**Status:** Planned  
**Goal:** Distinguish « mitady / cherche » (demand) from « amidy / vente » (supply) in mixed Malagasy–French text.

### Notes

- Aliases already exist on `Product`; extend them from real phrases
- Photo-only posts are a later slice (vision), not the first NLP slice

---

## v6 — Product UX

**Status:** Planned  
**Goal:** History charts, category filters, and a Tana vs regions split once we have time series.

---

## v7 — Installable app

**Status:** Planned  
**Goal:** Harden PWA (offline shell) and add Capacitor Android (Play Store), iOS if needed.

---

## v8 — Marketplace partners

**Status:** Planned  
**Goal:** Ingest **search logs** from local marketplaces (strongest “what people look for” signal). Partnership-first, not scraping.

---

## Non-goals (until the roadmap says otherwise)

- Scraping Facebook, Instagram, WhatsApp, or private groups
- Meta Content Library as a commercial app backend (research cleanroom only)
- Using Radar.com Places as a catalogue of Malagasy markets
