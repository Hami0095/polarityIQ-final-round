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
- `rag/` — ingestion, chunking (structured filters vs. semantic text), retrieval, and a
  code-enforced grounding/citation-check layer.
- `app/` — non-technical UI (Streamlit) for querying the dataset.
- `data/` — `raw/` (source pulls), `interim/` (candidates, pre-validation), `final/`
  (delivered dataset + validation + audit logs).
- `logs/` — structured run logs that the methodology summary is generated from.
- `docs/` — stack choices, chunking strategy, live query transcripts.

## Setup

```
pip install -r requirements.txt
```
