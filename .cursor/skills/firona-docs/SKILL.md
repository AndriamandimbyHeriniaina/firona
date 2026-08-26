---
name: firona-docs
description: >-
  Navigates Firona documentation split by function and keeps versions in sync.
  Use at the start of every Firona task, when the user mentions README, docs,
  INDEX, versions, v1–v8, or documentation structure.
---

# Firona docs

## Before work

Read (full files):

1. `README.md`
2. `docs/INDEX.md`
3. `docs/versions.md`
4. `docs/product.md` if the task is product/legal/scope
5. The **function** doc named in INDEX for the files you will edit

Then follow the matching **service skill** (`firona-nginx`, `firona-backend`, `firona-frontend`, `firona-workers`, `firona-data`, `firona-compose`). Do not put nginx rules in the backend skill.

## After shipping

Update the function doc + `docs/versions.md` + `docs/INDEX.md` dates. Update `README.md` if commands or ports changed. Never rewrite past versions.
