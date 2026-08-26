# Legal sources

Policy for **what Firona may read**. Collectors (v3) must call `assert_can_collect(source)` before any HTTP. There is no “scrape everywhere” path.

## Matrix

| Kind | Consent | Collectable now (v3 target) | Notes |
| --- | --- | --- | --- |
| `meta_ads` | No (public Ads Library) | **Yes** | Madagascar commercial/issue ads only via official API |
| `google_trends` | No (public Trends) | **Yes** | `geo=MG` only |
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

## Store vs never store

**Store:** source id, timestamps, aggregate counts, `TrendSnapshot` scores, public ad/trend identifiers if the API gives them.

**Never store:** names from comments, phone numbers, Messenger bodies, private-group posts, scraped HTML, tokens in `TrendSnapshot`.

## Revocation

Admin (or later an API): `Source.revoke_consent()`. Sets `consent_granted=False`, `consent_revoked_at=now`. Existing snapshots **stay** (history). New collects must stop immediately.

## First partners to ask (pages/groups)

Not collected until a later version; track them as `Source` rows with consent flags:

- Boutique GSM Analakely / Soarano (pages)
- Groupes de vente **publics** whose admins agree in writing
- Never: private braderies without admin agreement

## Code

- `apps/sources/policy.py` — `assert_can_collect`, `collectable_sources()`
- `Source.can_collect` / `block_reason` / `revoke_consent` / `mark_success` / `mark_error`
- Task `audit_sources` (no outbound HTTP)
