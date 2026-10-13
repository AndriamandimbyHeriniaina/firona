# Legal sources

Policy for **what Firona may read**. Collectors (v3) must call `assert_can_collect(source)` before any HTTP. There is no “scrape everywhere” path.

## Matrix

| Kind | Consent | Collectable now (v3) | Notes |
| --- | --- | --- | --- |
| `meta_ads` | No (public Ads Library) | **Yes** | Graph `ads_archive`, `ad_reached_countries=['MG']`. Commercial ads are **not** in the archive outside EU/UK; MG is political/issue ads. Token: `META_ADS_ACCESS_TOKEN`. |
| `google_trends` | No (public Trends) | **Yes** | RSS `?geo=MG` only. Google does not publish a daily RSS for MG today (HTTP 400); the job records `last_error` and does not query another country. |
| `facebook_page` | **Yes** (page owner / Page token) | Not yet | Record the partner; collect in a later slice |
| `facebook_group` | **Yes** (admin) | Not yet | Public group + written admin consent |
| `tiktok` | Public trends API if any | Not yet | After v3 |
| `marketplace_partner` | **Yes** (contract) | Not yet | Search logs only, v8 |

**Never (no kind, no code path):** scraping Facebook / Instagram / WhatsApp / Messenger / private groups / Marketplace HTML. Meta Content Library is research-only, not this app.

## Switch (the only one)

A Celery task may collect **iff** `source.can_collect` is true:

1. `kind` is in the collectable set (`meta_ads`, `google_trends` for v3)
2. `is_active` is true
3. If the kind requires consent: `consent_granted` and `consent_revoked_at` is empty

Otherwise `CollectionDenied` — skip, log, do not HTTP.

Since v4 the gate is checked **before every HTTP attempt**, retries included, with the flags re-read from the database: revoking consent in the admin stops a run that is already retrying.

## Store vs never store

**Store:** source id, timestamps, aggregate counts, `TrendSnapshot` scores, public ad/trend identifiers if the API gives them.

**Never store:** names from comments, phone numbers, Messenger bodies, private-group posts, scraped HTML, tokens in `TrendSnapshot`.

Tokens and secrets are redacted (`apps/sources/redact.py`) before anything lands in `Source.last_error` or `CollectionRun.detail`, and `httpx` request logging is off (it prints full URLs). The public API exposes a source's `health` (`ok` / `error` / `never` / `blocked`), never its error text.

## Revocation

Admin (or later an API): `Source.revoke_consent()`. Sets `consent_granted=False`, `consent_revoked_at=now`. Existing snapshots **stay** (history). New collects must stop immediately.

## First partners to ask (pages/groups)

Not collected until a later version; track them as `Source` rows with consent flags:

- Boutique GSM Analakely / Soarano (pages)
- Groupes de vente **publics** whose admins agree in writing
- Never: private braderies without admin agreement

## Code

- `apps/sources/policy.py` — `assert_can_collect`, `collectable_sources()`, `TRENDS_GEO` / `ADS_REACHED_COUNTRY` (`MG`)
- `Source.can_collect` / `block_reason` / `revoke_consent` / `mark_success` / `mark_error`
- Task `audit_sources` (no outbound HTTP)
- Collectors: `apps/trends/collectors/` (`gated_request` always calls `assert_can_collect` first, and again before each retry)
- Hourly request budgets per source: `COLLECT_BUDGET_*` (see [workers.md](workers.md))
- Raw rows: `CollectedSignal`. Scores: `TrendSnapshot`
