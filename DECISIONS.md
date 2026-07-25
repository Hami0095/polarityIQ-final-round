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

## 2026-07-25 — Response to pilot review: source cap enforcement + contact intelligence

User reviewed the 9-firm pilot, independently re-verified three load-bearing claims (all held
up), and approved the judgment quality. Gave two blocking work items before scaling to 50:
(1) enforce the 35% source cap in code, not just print a warning, and diversify beyond EDGAR;
(2) improve contact coverage without ever loosening the "only checkable, never guessed"
standard, plus add legibility fields so sparsity reads as honest rather than lazy.

**Work item 1 — done.**
- `dataset/assemble.py` now has `enforce_source_cap()` / `SourceConcentrationError`: assembly
  hard-fails (raises, writes nothing) if any `discovery_source` exceeds 35% of the qualifying
  set. Confirmed it actually fires: ran it against the original 9-firm pilot (EDGAR at 67%)
  and it raised and refused to write the CSV, before any new data was added.
- Added 9 more qualifying firms across 6 new discovery-channel labels to dilute EDGAR:
  Deal/Transaction Press (Real Capital Solutions / Arsenault Family Office), Regional Business
  Press (Rock/Dan Gilbert Family Office, Angeles Family Office), University Donor/Foundation
  Bridge (Pritzker Group / PSP Partners), Liquidity-Event Tracing (BLN Capital),
  Conference/Association Speaker List (Bedrock Group — see caveat below), and Regional/Sector
  Directory via billionaire-family-office lists (Excession/Musk, Willett Advisors/Bloomberg,
  Cascade Investment/Gates).
- **Final source mix at n=18 qualifying + 1 rejected** (table, as requested):

  | Source | Count | % |
  |---|---|---|
  | SEC EDGAR Form D | 6 | 33% |
  | Regional/Sector Directory (billionaire family office lists) | 3 | 17% |
  | ProPublica Nonprofit Explorer (990) | 2 | 11% |
  | Regional Business Press | 2 | 11% |
  | Press search (WebSearch, ad hoc) | 1 | 6% |
  | Deal/Transaction Press | 1 | 6% |
  | University Donor/Foundation Bridge | 1 | 6% |
  | Liquidity-Event Tracing | 1 | 6% |
  | Conference/Association Speaker List | 1 | 6% |

  EDGAR is now 33%, under the enforced 35% cap. Did not add further EDGAR candidates in this
  pass per the instruction to hold it at ~6 until other channels caught up — they now have.

**Work item 2 — done, with the ceiling named explicitly, not fought.**
- Added `contact_actionability` (computed, not authored, from what actually survived
  validation — see `Firm.contact_actionability()` in `dataset/schema.py`) and `checked_at` on
  every `SourcedField`.
- **Contact coverage at n=18** (as requested, by field and by classification):

  | Group | n | Named principal | Firm-level contact | Direct principal contact |
  |---|---|---|---|---|
  | All | 18 | 13/18 (72%) | 6/18 (33%) | 1/18 (6%) |
  | SFO | 10 | 10/10 (100%) | 3/10 (30%) | 1/10 (10%) |
  | MFO | 7 | 3/7 (43%) | 3/7 (43%) | 0/7 (0%) |
  | Unable to Determine | 1 | 0/1 | 0/1 | 0/1 |

  This is exactly the inverse-opacity pattern flagged as expected: SFOs have 100% named-
  principal coverage (their principals are public, well-known figures — that's *why* they're
  discoverable at all) but only 1 direct contact across all 10; MFOs are more likely to publish
  a general office line but less likely to have one obviously identifiable "the" principal.
  The single direct-contact hit (Real Capital Solutions/Arsenault, see below) came from a firm
  small and self-promotional enough to publish individual staff phone numbers — not
  representative of the market, and said so rather than implying this is a repeatable rate.

- **A real near-miss worth reporting exactly as asked:** WebFetch's summary of
  `realcapitalsolutions.com/team/` reported a plausible `firstname@domain`-style email for
  every team member. Before using any of them, I fetched the raw HTML directly with `requests`
  and grepped for `@` — **none of those emails exist in the page's actual source.** The site
  uses Cloudflare email obfuscation; WebFetch's summarizing model filled in a
  plausible-looking placeholder instead of reporting "email present but obfuscated." Had I
  trusted the tool's summary instead of checking raw source, I would have put fabricated
  emails into the delivered file with a "verified" label — exactly the disqualifying failure
  mode named in the brief. Caught it, left all those emails blank, and used only what was
  actually verifiable in raw HTML (real phone numbers and LinkedIn URLs for named staff, which
  did check out character-for-character). **Lesson applied going forward: any contact value
  sourced via WebFetch's summary gets cross-checked against raw HTML before inclusion, not
  just trusted.** This also means I should go back and spot-check the Virtus/PointOne/BLN/
  Bedrock firm-level emails from the original pilot the same way — did so during this pass
  (see below), and those four were genuinely present in raw HTML, not fabricated.
- **A second tooling bug caught in this pass:** the email validator's MX/DNS check was
  treating network timeouts the same as NXDOMAIN (definitive "no such domain"). Four real,
  previously-verified emails (Virtus, PointOne, BLN Capital, Bedrock) got transient DNS
  timeouts on a later run and were about to be silently nulled and logged as "undeliverable" —
  which would have been false. Fixed `validation/checks.py` to retry on timeout and only treat
  NXDOMAIN/NoAnswer as a genuine failure; timeouts now raise `MXCheckInconclusive` and the
  affected field is left untouched (with a visible warning printed), not silently nulled. This
  is the kind of validation-layer bug that would have quietly corrupted good data if I hadn't
  cross-checked the "failures" by hand.
- **Why the contact_audit_log is empty at n=18, and why that's not the same problem the user
  flagged:** every contact value included in this batch was pre-filtered by manual raw-HTML
  verification before it ever reached the validator (see the two catches above) — so nothing
  reached assembly that was likely to fail. This is different from "validation never rejects
  anything" — it's "I already did validation's job by hand during enrichment before handing
  it off." At n=50, with far more contact fields harvested from more team pages under less
  individual scrutiny per record, I expect the audit log to actually populate — flagging this
  now rather than let an empty log look like validation is decorative.
- **Things that didn't pan out (reported as asked, not quietly dropped):**
  - Chamber-of-commerce / economic-development relocation-announcement search: returned zero
    usable family-office leads — generic chamber content only. Not pursuing this specific
    query pattern further; will try state-level "site selection" / corporate relocation press
    instead if directory coverage needs more volume.
  - Kimmelman/Energy Capital Partners: found a real 990-linked family foundation, but ECP
    itself is a multi-LP private equity fund manager, not a clean single-entity family office,
    and no distinctly-named Kimmelman family office turned up. Dropped rather than force-fit a
    PE fund manager into the dataset as if it were a family office.
  - Pritzker Group vs. PSP Partners: my research did not cleanly resolve whether these are one
    entity or two related-but-distinct Pritzker-family vehicles (Anthony's side vs. Penny's
    side) — recorded as one combined record with that ambiguity stated in `blind_spots` rather
    than guessing a cleaner structure than what I actually confirmed. Will need a dedicated
    pass to split this correctly before final delivery if both should count separately.
  - Geller and Bedrock's classification is complicated by both having been acquired by Corient
    (Jan 2025 and 2026 respectively) — kept both as MFO records with the acquisition uncertainty
    stated in `blind_spots`, rather than either dropping them or pretending they still
    obviously operate independently.
  - No point in this pass where I was tempted to invent a value to hit a number — the closest
    was wanting to mark the Real Capital Solutions emails "verified" straight from the WebFetch
    summary before I did the raw-HTML check; that impulse is exactly what the raw-HTML
    cross-check exists to catch, and I'm treating "always cross-check WebFetch's contact
    extractions against raw source" as a standing rule from here on, not a one-time fix.

**Files:** `dataset/pilot_records_batch2.py`, `dataset/pilot_records_batch3.py`,
`dataset/assemble.py` (cap enforcement, contact coverage reporting), `validation/checks.py`
(MX timeout fix), `tests/test_assemble.py`. `data/final/pilot_dataset.csv` now has 18 rows.

**Not yet done, holding for user sign-off before proceeding:** scaling this same process to
the full 50. The mix and coverage above are for review first, per the checkpoint instruction.
