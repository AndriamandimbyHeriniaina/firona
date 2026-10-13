# Product

Firona is a **demand radar** for articles on the Malagasy market: **now**, **past**, and **likely next**.

It is not a map of physical markets. Radar.com Places is not the catalogue.

## Engines (do not collapse)

Three roles stay separate. Django never collects and never runs the model.

```
Legal sources → Celery collect (v3) → Postgres raw / snapshots
                      ↓
              Local LLM organise (v5)
                      ↓
              Django API → Vue radar
```

| Role | Process | When |
| --- | --- | --- |
| Serve the radar | Django `backend` | now |
| Fetch legal signals | Celery `worker` + `beat` | **v3** (shipped), hardened in **v4** |
| Filter, classify, organise articles | Celery jobs calling a local LLM container | **v5** |

The article catalogue (`Product`) stays curated until a later slice. Collectors score known articles; they do not scrape a marketplace to invent the catalogue.

## Signals (legal only)

See [sources.md](sources.md). Short version: Ads Library + Trends `MG` are the only collectable kinds for v3. Facebook pages/groups need consent and are **not fetched yet**. Scraping is forbidden.

## Local LLM (v5, planned)

Free, offline, Docker-only. The browser never talks to it. Jobs are slow on CPU on purpose: beat processes batches, not request/response.

| Choice | Value |
| --- | --- |
| Runtime | Ollama (`ollama/ollama` Compose service `llm`, not shipped yet) |
| Instruct model | `qwen3.5:4b` (Q4, ~5 GB RAM). Fallback: `gemma3:4b` if Malagasy coverage is weak |
| Pipeline | Lexicon first (`mitady` / `cherche` vs `amidy` / `vente`), LLM only on ambiguous text |
| Later | Same Ollama for embeddings (`nomic-embed-text`) to cluster aliases |
| Out | Cloud APIs, 70B models, vLLM, running inference inside Django views |

GPU is optional (WSL NVIDIA if present). CPU is enough.

Roadmap dates and slice goals: [versions.md](versions.md).

## Non-goals (until versions.md says otherwise)

- Facebook/Marketplace scraping
- Using Radar.com as a market directory
- Auth / multi-tenant (not in v1)
- Cloud LLM APIs as the organiser
