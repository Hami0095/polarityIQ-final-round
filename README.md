# Family Office Dataset + Micro-RAG

A verified dataset of 50 real family office records (firms + principal contacts + recent
signals), built through a multi-source, source-logged discovery/enrichment/validation
pipeline, plus a Micro-RAG app for querying it in natural language with code-enforced
grounding.

See [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for the assignment and [DECISIONS.md](DECISIONS.md)
for the running log of choices and tradeoffs made while building this.

## Layout

- `discovery/` — source connectors (SEC EDGAR, ProPublica 990, web search) that output
  candidate firms tagged with `discovery_source`.
- `enrichment/` — per-candidate lookups that fill firm/principal/signal fields, each tagged
  with its source.
- `validation/` — email/phone/AUM/thesis verification checks; failed cells get nulled, not
  just flagged.
- `dataset/` — shared schema, final assembly (qualifying filter, dedup, cut to 50), CSV/XLSX
  output, methodology summary generated from run logs.
- `rag_app/` — the actual deployed Micro-RAG: TF-IDF retrieval, structured filters, template
  synthesis, and a code-enforced grounding/citation-check layer, as a standalone Vercel
  serverless function. Live at https://ragapp-sand.vercel.app. See `documentation-note.md` for
  the stack write-up.
- `data/` — `raw/` (source pulls), `interim/` (candidates, pre-validation), `final/`
  (delivered dataset + validation + audit logs).
- `logs/` — structured run logs that the methodology summary is generated from.
- `docs/` — live query transcripts against the deployed app (`live_queries.md`).
- `app/`, `rag/` — early-plan stub packages (empty `__init__.py` only). Superseded by
  `rag_app/`; not a Streamlit UI, not built out. Left in place rather than silently deleted,
  flagged here so the layout description matches what's actually in the repo.

## Setup

```
pip install -r requirements.txt
```
