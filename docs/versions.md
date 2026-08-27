# Versions

Source of truth for **what shipped** and **what is next**. Do not delete past versions: mark them done and append.

| Field | Value |
| --- | --- |
| Current version | **v2 — Legal source strategy** |
| Last updated | 2026-08-27 |

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

**Status:** Planned  
**Goal:** Celery jobs filling `TrendSnapshot` from Ads Library + Google Trends `MG`.

### Planned

- Beat schedule for `meta_ads` and `google_trends` only
- `assert_can_collect` before any outbound HTTP
- `mark_success` / `mark_error` on each run
- Snapshots attached to **existing** `Product` rows (seed / admin catalogue)

### Out of scope

- Local LLM / Ollama (v5)
- Auto-creating articles from raw ads or queries
- Facebook page/group fetch even with consent
- Retries, rate-limit budgets, queue lag on health (v4)

### Decisions

- Collect is a Celery engine, not Django views
- Raw fetch and later AI organise stay different jobs
- Demo seed remains until collectors produce real scores

---

## v4 — Robustness of services

**Status:** Planned  
**Goal:** Retries, idempotent snapshots, timeouts, queue lag on health, rate-limit budgets.

Collectors stay reliable before we add a model. No LLM in this slice.

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
