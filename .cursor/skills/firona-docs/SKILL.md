---
name: firona-docs
description: >-
  Loads Firona project context from README.md and DOC.md, then keeps those
  files in sync after work ships. Use at the start of every task in this
  repository: coding, architecture, Docker, Django, Vue, PWA, radar, trends,
  collectors, sources, Celery, or documentation. Use whenever the user mentions
  Firona, versions (v1, v2, …), README, or DOC.md.
---

# Firona docs (always)

## Before any work

Read both files with the Read tool (full files, not grep snippets):

1. `README.md` — how to run the stack
2. `DOC.md` — current version, decisions, roadmap

Do this even if the user did not mention docs. If a file is missing, stop and say so.

## While working

- Stay inside the **Current version** in `DOC.md` unless the user explicitly starts the next version.
- Do not implement a later version “while we are here”.
- Do not add Facebook/Marketplace scraping. Allowed sources are only those listed in `DOC.md`.
- UI strings: French. Code comments and docstrings: English (with a short example).
- Reply to the user in French.

## After shipping

In the **same change** as the code:

1. Update `DOC.md`: status, in/out of scope, **Decisions**, **Follow-ups**, **Last updated**, **Current version** if a version completed or started.
2. Update `README.md` if ports, commands, services, or setup changed.
3. Never rewrite past versions; mark them done and append.

## Version bumps

Only move **Current version** when the user agrees the slice is done or that the next version starts. Planned sections in `DOC.md` stay thin until then.
