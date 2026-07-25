# Decisions Log

Running log of choices, tradeoffs, and uncertainty as this project is built. Updated as work
happens — not polished retroactively.

## 2026-07-25 — Project kickoff

- **Environment constraints confirmed with user before starting:**
  - No paid data-provider APIs (Clearbit/Apollo/people-data). Discovery and enrichment rely on
    free public sources: SEC EDGAR full-text search, ProPublica 990 API (public charity
    filings), general web search, and direct fetches of firm/press/directory pages.
  - LinkedIn: no scraping (violates ToS, real legal exposure). Only used as a discovery signal
    when a LinkedIn company/profile URL surfaces in public search results — the URL itself is
    recorded as a reference, not scraped content.
  - Build and test locally first. Deployment to a public host happens after the app works
    end-to-end locally, once the user picks a host and supplies credentials.

- **Found a pre-existing file in the repo root: `FO-MAX-data-sample-2.0.xlsx`.** This is a
  vendor sample dataset with a similar-shaped schema (firm description/thesis/sectors,
  contact name/title/email/phone with validation-status codes) covering ~20+ real firms
  (e.g. Walton Family Foundation, Emerson Collective, Third Lake Capital). It is **not** used
  as a data source. It lacks AUM, SFO/MFO classification + evidence, discovery_source,
  confidence scoring, and signals — all required by this project's proof rules. Treated purely
  as schema inspiration for column naming, then set aside. None of its rows will appear in the
  delivered dataset unless independently re-discovered and re-verified through this project's
  own pipeline.

- **Network check:** direct `requests` HTTP calls work in this environment (confirmed against
  sec.gov, got a 403 which is expected without a proper SEC-required User-Agent header — SEC
  requires a descriptive UA with contact info on all automated requests, will set that).
  This means EDGAR full-text search and the ProPublica 990 API can be called directly via
  Python rather than only through the higher-latency web-search tool — faster and more
  reliable for structured API sources.

- **Repo scaffolding:** Python project, real incremental git history (scaffold commit, then one
  commit per pipeline layer as it lands), module boundaries per the brief: `discovery/`,
  `enrichment/`, `validation/`, `dataset/`, `rag/`, `app/`.
