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

- **SEC EDGAR full-text search confirmed working** as a discovery source for Form D filings
  (private placement notices) — searching for `"family office"` restricted to `forms=D`
  returns 261 hits, e.g. "Wilshire Private Markets Family Office Fund II", "TFO Purpose Fund".
  Requires a descriptive `User-Agent` header per SEC's automated-access policy.
  **ProPublica Nonprofit Explorer API confirmed working** as a discovery source for
  foundation-side family offices (many single-family offices operate a linked private
  foundation that files a 990) — query `q=family+office` returns 33 orgs.

- **Dropped sentence-transformers/chromadb from the RAG stack.** This machine's disk had only
  ~16GB free (pip's HTTP cache alone was consuming 8.3GB, later purged) and installing
  torch + sentence-transformers risked filling it again along with a slow install. For a
  50-record dataset, a full neural embedding stack is disproportionate anyway. Using
  scikit-learn's TF-IDF vectorizer for the semantic-text half of retrieval instead, paired
  with SQLite for the structured/filterable half (AUM, sector, state, classification). This
  is a legitimate lighter-weight semantic retrieval method, not a shortcut that weakens
  grounding — the grounding control is enforced by the citation-checking layer regardless of
  which vectorizer produced the candidate set.

## 2026-07-25 — Pilot batch (9 qualifying + 1 rejected)

Per user's request, built and verified a 9-firm pilot end-to-end (discovery through
validation/assembly) before committing to running the same process across all 50, so data
quality could be reviewed first. See `dataset/pilot_records.py`, `dataset/assemble.py`,
`data/final/pilot_dataset.csv` / `pilot_rejected.csv` / `pilot_contact_audit_log.csv`.

- **Source concentration flag fired as designed:** SEC EDGAR Form D contributed 6/9 (67%) of
  the pilot — well above the brief's ~30-40% threshold. This is expected at n=9 with only 3
  source classes exercised so far (EDGAR, ProPublica, one press search). Scaling to 50 will
  need to lean harder on WebSearch-driven press/conference/directory discovery to bring EDGAR's
  share down; flagging this now rather than after the fact, as instructed.
- **Classification honesty demonstrated on purpose, not just claimed:** Pathstone and Geller
  are both widely called "family offices" in casual industry usage but are large multi-family
  offices by evidence (many client families, not one) — classified MFO. White Knight Family
  Office LLC has "family office" in its name and a real SEC Form D filing but no first-party
  site or affirmative description found — classified Unable to Determine rather than assumed
  SFO. Point72 (Steven Cohen) originated as a family office but has accepted outside capital
  as a registered adviser since 2018 — excluded entirely via the rejected/audit log rather than
  included and relabeled.
- **Contact honesty:** only firm-level general office emails/phones that were directly listed
  on a firm's own website were included (Virtus, PointOne), and both passed real syntax+MX
  (email) and format/region (phone) checks before being written to the delivered CSV. No
  individual principal email or phone was fabricated or inferred — every principal's
  work_email/direct_phone was left "could not verify" in this pass since no checkable source
  (team page, filing, LinkedIn profile with a listed email) turned one up.
- **AUM sourcing discipline:** where a number came from a secondary aggregator citing a primary
  filing (PointOne's $327M via fintrx citing SEC ADV) it's tagged Medium confidence, not High,
  because the primary IAPD page couldn't be fetched directly (JS-rendered). Where a number was
  corroborated across 2+ independent press domains (Pathstone, Geller) it's tagged High. Virtus
  Family Office's 13F-derived ~$78M was deliberately *not* used as its AUM figure — 13F only
  captures certain US equity positions and would understate/mischaracterize true AUM, so that
  field was left blank rather than presented as a verified number.
- **Address discrepancy caught, not silently resolved:** PointOne Family Office had two
  different HQ addresses across sources (its own site vs. a search snippet); used the
  first-party site's address and documented the conflict in `blind_spots` instead of picking
  one without comment.
- **Next step:** awaiting user review of the pilot before scaling the same discovery →
  enrichment → validation process to the full 50, adding more WebSearch-driven source classes
  (state UHNW directories, conference speaker/sponsor lists) to fix the EDGAR concentration.
