---
name: firona-sources
description: >-
  Applies Firona legal source policy (no scraping, Source.can_collect gate).
  Use when editing Source, policy.py, collectors, consent, Ads Library,
  Google Trends, Facebook pages/groups, or docs/sources.md.
---

# Firona sources

Read `docs/sources.md` before changing collection rules.

## Do

- Call `assert_can_collect(source)` before any outbound HTTP.
- v3 fetch kinds: `meta_ads`, `google_trends` only.
- On revoke: `source.revoke_consent()` — keep `TrendSnapshot` history.

## Do not

- Scrape Facebook, Marketplace, Messenger, or private groups.
- Treat Meta Content Library as an app backend.
- Fetch `facebook_page` / `facebook_group` in v3 even if consent is granted.

## After change

Patch `docs/sources.md`.
