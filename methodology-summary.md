# Methodology Summary — Family Office Dataset + Micro-RAG

*Final numbers as frozen, filled from `data/final/pilot_dataset.csv` at n=50 (2026-07-26).*

---

## What the system does

Five discovery channels feed a candidate pool. An entity-type filter rejects non-family-office
entities before classification is attempted. Websites and structured records are resolved, then
classification runs against affirmative evidence — never against a firm's name. Every extracted
value passes a two-part evidence gate. Assembly enforces source-concentration caps and hard-fails
rather than warns. A deployed Micro-RAG serves the result with the same gate governing what a user
can be told.

**Final dataset: 50 qualifying records.**

- Classification: 29 Multi-Family Office, 4 Single-Family Office, 17 Subtype unconfirmed
- Source mix: SEC Form ADV 25 (50.0%), Wikidata 19 (38.0%), SEC EDGAR 13F 6 (12.0%)
- Coverage (n=50): named principal 32, firm phone 32, firm email 11, direct principal
  contact 7, regulatory AUM 30, dated signal 29
- Contact actionability distribution: Named principal + firm-level contact 19, Firm-level
  contact only 9, No reachable contact 9, Named principal + direct contact for that
  principal 7, Named principal, no contact 6
- Evidence class: A 16, B 1, C 16, D 3, remainder 14 unlabelled — these 14 carry a determinate
  SFO/MFO classification reached directly (12 via first-party website phrase-match, 2 via
  first-party self-description found on their own homepage — Mayfair, Paulson & Co.), so no
  evidence-class tier applies; the tier exists for records whose family-office status is
  confirmed but whose SFO/MFO subtype is not.

## Discovery: which source did which job

| Channel | What it can establish | What it cannot | Candidates | Qualifying |
|---|---|---|---|---|
| SEC Form ADV bulk | Existence, filed website, address, phone, client structure, regulatory AUM | Single-family offices (exempt — see below) | 73+ | 25 |
| SEC EDGAR 13F index | Operating investment entities, signer name/title/phone | Classification | 68 | 6 |
| Wikidata SPARQL | Structured third-party classification | Contact data | 31+ | 19 |
| SEC EDGAR Form D | **Verification only — demoted, see Finding 4** | Discovery | 43 | 0 |
| ProPublica 990 | Family foundations | Operating-entity bridge | 58 | 0 |

Two channels produced nothing and are reported as such rather than quietly dropped. Form D was
demoted on evidence. ProPublica's candidates proved to be foundations and industry networks with
"family office" in the name coincidentally — cross-referencing all 58 against the ADV roster
produced zero matches above threshold.

### The regulatory asymmetry that shaped this file

Single-family offices are largely **exempt from Advisers Act registration** under the family
office exemption, Rule 202(a)(11)(G)-1. They therefore do not appear in Form ADV — the one channel
that reliably supplies a filed website, contacts, and client-structure data.

This is the single largest force acting on the file's composition, and it explains the 4/50 SFO
count directly. It is not a gap in the pipeline; it is the regulatory reason this segment is hard
to find. The firms that are most valuable to a buyer are precisely the ones the disclosure regime
does not require to be visible.

## Evidence model: what qualifies a firm

A record qualifies only on **affirmative evidence** that the firm is a family office. Never a
name, never a source's reputation, never inference from serving wealthy clients.

- **Class A — structured third-party classification.** Wikidata `P31`/`P452` = Q751314, verified
  live against the API, with no further corroboration found (no English Wikipedia article, or an
  article that didn't independently confirm the claim). 16 records.
- **Class B — third-party published description.** A full Wikipedia article (fetched via
  `action=query&prop=extracts&explaintext`, not just the summary endpoint) contains an
  affirmative, firm-anchored statement of family-office status. 1 record (Bessemer Trust — "a
  private, independent multi-family office...").
- **Class C — regulatory client-structure corroboration.** The firm's filed legal name asserts
  family-office status, and its Form ADV Item 5.D client composition (HNW individuals only, no
  institutional client categories, count within the stated ceiling) is consistent with that
  assertion. **Corroborating rather than independent, and the weakest class in this file.**
  16 records rest on Class C alone.
- **Class D — first-party self-description, manually verified.** Affirmative single/multi-family
  language found in the firm's own website text, but not (yet) confirmed by the automated
  anchor-gated classifier itself — Destiny, Alpha Capital, Hampshire. 3 records.

The remaining 14 records carry no evidence-class tag because their SFO/MFO subtype is already
determined directly. 13 of the 14 (12 MFO, 1 SFO — Mayfair) pass the deterministic, anchor- and
bio-transition-guard-gated phrase classifier against first-party website text, including Element
Pointe and Mayfair, both resolved via a bounded 1-hop internal crawl that found genuine
self-description pages the earlier fixed-path guesses had missed. **The 14th, Paulson & Co., is
a disclosed exception:** its Single-Family Office classification rests on a manual reading of its
Wikipedia article ("the firm has operated as a family office managing Paulson's personal
wealth") rather than a passing run of the automated classifier — re-running that exact text
through `classify()` returns `UNKNOWN`, because "managing [a named person]'s personal wealth"
doesn't match the `SFO_MARKERS` regex set (which requires "family's own wealth" phrasing). This
gap was found and flagged, not silently resolved; the classification stands on human judgment of
genuinely affirmative prose, not on the code path most other records in this file use. The
evidence-class tier exists specifically for "confirmed family office, subtype unresolved"
records; a record with a resolved subtype doesn't need it.

**On Class C's limitation, stated plainly:** the Item 5.D rule tests client *structure*, not
family-office status. A boutique adviser with a small HNW-only book satisfies it. What makes it
defensible is that the candidate pool was name-filtered first, so it is self-identification plus
structural corroboration — not structure alone. It is disclosed as the weakest tier precisely
because a reviewer should be able to weigh it accordingly.

### The threshold, and why it exists

Inclusion rule: HNW individual clients > 0, zero clients in every institutional category, HNW
count ≤ 60. The ceiling is a judgment call, and it exists for a measurable reason: without it, a
broadened keyword pull returned **558 generic retail RIAs** that satisfied the structural test.
Subtype: SFO if HNW ≤ 5, MFO otherwise, `Subtype unconfirmed` where ambiguous. Subtype is never
forced.

## Terminology-driven 13F expansion: a null result, kept

A cycle was run to test whether broadening the 13F name-filter vocabulary beyond the literal
"family office" would surface qualifying candidates. **Cycle 1 first checked the premise against
the confirmed pool itself: 30 of the 33 confirmed records use "Family Office(s)" verbatim in
their legal name; none use "Family Capital," "Family Holdings," "Family Partners," "Family
Group," "Family Investments," "Family Trust," or "Family Enterprises."** The hypothesized
vocabulary isn't attested in what actually qualified — a real finding, reported before proceeding
rather than after.

Cycle 2 re-filtered the already-discovered 13F candidate pool (68 "family"-substring filers,
cached from the original discovery pass — no new bulk fetch needed, since a bare "family" filter
is already a superset of every more specific pattern) against that vocabulary: **7 new
candidates** (Alpha Family Trust, American Family Investments, Family Capital Management, Family
Capital Trust Co, Safe Harbor Family Capital, TLT Family Holdco, West Family Investments), none
previously in the dataset or rejected list.

Cycle 3 ran every candidate through the same bar as the existing 50, no relaxation: all 7 passed
the entity-type filter (no fund-vehicle or institutional-service markers). 2 had an exact ADV
match — both failed Item 5.D on the same rule that governs every other record in this file
(Family Capital Management: 131 HNW clients, over the 60-client ceiling, plus nonzero charitable
and corporate clients; Safe Harbor Family Capital: 10 HNW clients but a nonzero charitable-client
count) — a institutional client, however small, disqualifies regardless of HNW count. Family
Capital Management's self-disclosed website was fetched and run through the classifier with both
guards anyway; it reads as a generic financial-planning practice, no affirmative single/multi-
family language. The other 5 had no ADV match and no resolvable website — no evidence available
by any channel checked.

**Result: 0 of 7 candidates qualified.** All 7 logged to `pilot_rejected.csv` with the specific
reason each failed. No new 13F record was added, so no ADV record was held back, and the file's
composition, classification split, and evidence-class distribution are **unchanged from the
prior freeze** — re-verified via `assemble()` (cap still fires correctly at exactly 25/50 =
50.0%) and the live 15-query log (identical to the prior run). This cycle is recorded because a
tested hypothesis that didn't pan out is still a real result, not because it changed the file.

## 13F holdings deltas as dated signals

For the 6 firms discovered via the SEC EDGAR 13F channel, the two most recent 13F-HR
information-table filings were fetched and diffed for quarter-over-quarter position changes.
This does not touch classification or discovery — it deepens the `signal` fields on records
already in the file.

**Labeling, deliberately narrow:** a delta is recorded as "New/Exited/Increased/Decreased
13F-reportable position in [issuer], quarter ending [date]" — never as "new investment" or
"conviction," for the same reason 13F holdings were already refused as an AUM proxy for Virtus
earlier in this build: a 13F delta is evidence of a reportable position change, nothing more. It
can result from rebalancing, redemptions, corporate actions (mergers, spinoffs, splits), or a
custodian/sub-adviser change. 13F itself covers only certain US equity holdings (not private
holdings, real estate, bonds, or cash) and is filed up to 45 days after quarter end, so a signal
reflects a position as of the reporting date, not current holdings. This caveat is attached to
every affected record's `blind_spots` field, not stated once and assumed remembered.

**Selection rule:** the top 3-5 most material changes per firm, ranked by reported position
value (new/exited position value, or the absolute dollar delta for a changed position),
combined across all three change types and taken by magnitude. A full delta table would be
dozens of minor line-item changes per firm — noise, not intelligence.

**Result:** 5 of the 6 firms had a computable delta (both had ≥2 filings) and produced 3-5
material signals each. **Capitol Family Office, Inc. produced zero** — verified directly against
both raw information-table XML filings (48 holdings each quarter, identical composition, no
position moved ≥25% in value) rather than assumed to be a parsing gap. No firm in this batch had
only one 13F-HR filing on file, so the "record and move on" case didn't arise here, though the
check was built to handle it.

This did not change any coverage count: the 5 firms with new deltas already carried one generic
"Form 13F-HR filed for period ending [date]" signal, counted in the existing `dated signal: 29`
figure — this pass replaced that with up to 5 specific, material signals each, deepening content
without changing coverage. `signal_3`/`signal_4`/`signal_5` columns (plus sources) were added to
the schema and CSV to hold them; the prior 2-signal cap was a delivery-format limit, not a
modeling one — `Firm.signals` was always an unbounded list internally.

## Classification is deterministic, not inferred

Phrase matching over source text with enforced word boundaries. Evidence span captured
automatically as a window of the real document. Both SFO and MFO evidence present, or neither →
`Subtype unconfirmed`.

Using a model for this added a fabrication surface, a yield ceiling, and no accuracy. The question
is `phrase in text`. Finding 5 covers what that cost before it was corrected.

## Validation

- **Cell level:** every high-value field carries source URL, evidence span, method, and check date.
- **Firm level:** affirmative evidence per the model above.
- **Two-part gate:** a value must be a literal substring of its evidence span, and the span must be
  a literal substring of the fetched source document. Failures are nulled and logged, not flagged
  and shipped.
- **Concentration:** enforced on both channel label and registrable source domain. Assembly raises
  and writes nothing on breach.
- **Email/phone:** syntax and MX checks, with definitive failure distinguished from inconclusive
  network error (Finding 8).

**On the concentration cap:** originally set at 35% assuming five producing channels. Three
produced. With three channels the arithmetic floor makes 35% unreachable, so the enforced cap was
raised to 50% — a deliberate, documented recalibration, not a silent disabling. ADV sits at exactly
25/50 = 50.0%. The cap was found to have been structurally bypassed for several rounds — edits
went through ad hoc CSV writes rather than the `assemble()` pipeline that actually invokes
`enforce_source_cap()` — and drifted to 52.1% before this was caught and fixed (Finding 7's
closing note). Once fixed, the file was rebalanced by dropping the two structurally weakest
ADV-only records (see Class C discussion) and expanded back to 50 by adding two qualifying
non-ADV records, all assembled through the real pipeline this time, with the cap verified to fire
correctly on a deliberate over-cap test before being trusted again. **No single source discovered
most of the file**, which is the rule the cap was proxying for.

## Findings that changed the build

Each is a real failure caught before it reached the delivered file.

**1 — A tool summary invented contact data.** WebFetch's summary of a firm's team page returned a
plausible `firstname@domain` address for every staff member. Raw-HTML fetch and grep showed none
existed — the site uses Cloudflare email obfuscation and the summarizer filled the gap. Evidence
spans were introduced as a structural control, and all contact values are now cross-checked
against raw source.

**2 — A model fabricated a value and its supporting quote together.** Testing extraction against a
page with a known answer, `minimax-m3:cloud` returned an invented AUM figure with a fabricated
evidence span, three times. The original single check (value-in-span) would have passed it. Added
`span_in_source`. Then evaluated a second model on the same known-answer page and switched
defaults on measured behaviour rather than preference.

**3 — A blocked search engine silently became "this firm does not exist."** DuckDuckGo began
returning a 202 challenge page mid-run. The connector could not distinguish that from a genuine
zero-result search, so consecutive real, resolvable firms were recorded as "no operating entity
found." Caught because rejections clustered and one was a firm with a known answer. `SearchBlocked`
now raises distinctly, the run halts, and 13 tainted records were purged rather than allowed to
become permanent via skip-if-processed.

**4 — SEC Form D full-text search is 74% fund vehicles.** Matching "family office" in Form D
overwhelmingly returns pooled products marketed *to* family offices — Wilshire, Lazard, Cubist,
Point72 Capital International — not operating family offices. Form D was demoted to a verification
source and an entity-type filter added upstream of classification.

**5 — My own gate was rejecting correct extractions.** Requiring a value to be a literal substring
of source is right for atomic fields and impossible for prose, which is inherently paraphrased.
Result: 0% yield on description and thesis, initially misread as a model ceiling. Gating is now
field-type aware — substring for atomic values, verbatim-quote selection for prose.

**6 — A field you don't surface is a field you don't validate.** Adding AUM to the rendered output
immediately exposed a record showing `$0&nbsp;Billion` — a broken extraction artifact with a
literal HTML entity that had sat in the CSV unnoticed for the entire build because nothing
displayed it.

**7 — Self-audit found a 20% error rate in website-phrase classification, and all three failures
were the same bug.** Sampling five records the way a reviewer would, two failed. A full audit of all
fifteen website-classified records found a third. Every one failed identically: **the phrase matched
somewhere on the page without referring to the subject firm.**

- *Element Pointe* — "single-family office" came from a contact-form dropdown question ("Select an
  option Yes No Do you have a single-family office today?"). Interface chrome, not a claim.
- *Arrowroot* — "multi-family office" described the CEO's **prior employer** in a bio.
- *Destiny* — the phrase came from a **blog headline about the industry**, on the firm's own site.

The instinct was to add a guard per failure mode. That is a denylist that grows forever, and Destiny
proved a third mode existed that hadn't been anticipated. So the classifier was changed to require
the marker phrase be **anchored to the subject firm**: a first-person voice marker ("we are", "we
serve", "our firm") or the firm's own name within ~100 characters — with the anchor invalidated if a
different organization's name intervenes. That last refinement came from testing rather than
assumption: Arrowroot's own name legitimately sat 88 characters before the false match, so a bare
name-in-window check still passed it. Form, nav, and footer elements are now stripped before text
reaches the classifier at all.

All three failures return UNKNOWN automatically, verified by re-running the classifier against
cached source — not patched in the CSV. Element Pointe and Destiny were downgraded to
`Subtype unconfirmed`; Arrowroot's classification stands on its own Item 5.D (595 HNW clients) with
the evidence text corrected.

Two records (Alpha Capital, Hampshire) pass manual verification but not the automated anchor check —
one self-refers by abbreviation, the other's self-description falls outside the window. Their
classification is retained with the automation gap disclosed per record rather than claimed as
automatic.

**A phrase appearing on a page is not the same as a page making a claim**, and a gate that passes is
not the same as a claim that is correct.

**8 — Validator bugs destroy good data too.** The MX check treated DNS timeouts as NXDOMAIN and was
about to null four correct, previously-verified addresses. Fixed to distinguish definitive failure
from inconclusive network error.

*Also caught and fixed:* a missing left word boundary matched "pathstone family" against the SFO
phrase "one family"; a domain guess accepted `pointone.com`, an unrelated AI billing startup, for
PointOne Family Office; Wikidata broadening returned Prague business-registry stubs that were
rejected as name-only inference; the website resolver stripped "family office" out of every domain
slug when roughly half these firms keep it verbatim; and the concentration cap was structurally
bypassed for several rounds because edits went through ad hoc CSV writes rather than the assembly
pipeline that invokes it.

## Provenance

> An earlier version of this pipeline had enrichment performed by hand — values researched
> interactively and written into Python literals, with code serving as a schema and validation
> wrapper. On audit this was found to violate the requirement that the record file be produced by
> the pipeline rather than manually assembled. The enrichment layer was rebuilt so that discovery,
> fetching, extraction, and classification all execute inside the program. The original
> hand-researched records were retained as a **ground-truth fixture for benchmarking only.** No
> hand-authored value appears in the delivered dataset.

**Benchmark run 2026-07-26** (`python -m benchmark.run`, re-run against the 18-firm hand-verified
fixture in `tests/fixtures/`):

- **Discovery recall: 7/15** ground-truth firms surfaced as a candidate by the two discovery
  channels that exist as code (`discovery/edgar.py`, `discovery/propublica.py`). The 8 misses are
  not pipeline bugs — each is attributed in the fixture to one of the ~7 other discovery channels
  named in the brief (press search, deal/transaction press, regional business press,
  conference/association speaker lists, a university donor bridge, SEC Form D, a 990
  operating-entity bridge) that were hand-research-only in the original pass and were never built
  as code. Recall against the two implemented channels' own intended scope, not the full 9, is
  the honest comparison.
- **Field-level agreement: not completed this pass.** The comparison requires a full live
  re-enrichment run (`run_enrichment()`), which re-fetches every candidate's source pages and
  timed out without completing in this session — consistent with the ADV bulk-download
  reliability issues logged earlier in this file. Reported as an incomplete check, not skipped
  silently: recall (a local, fast comparison) was run and is real; field agreement was not, and
  no contradiction count is asserted in its place.

Known contradiction retained rather than resolved: Form D issuer phone diverges from website phone
on multiple firms. Most likely a registered-agent or back-office line versus an operating line —
two real numbers, not an error on either side. Labelled, not silently reconciled.

## The 17 Subtype-unconfirmed records

All 17 rows below are **confirmed family offices** — each qualified on affirmative evidence per
the model above (a structured third-party claim, a filed legal name plus regulatory client
structure, or first-party self-description). None qualified on a name alone. The only thing
unresolved for these 17 is **which subtype** — single-family or multi-family. Resolution was
attempted (a domain-guess/website-search pass, and where a website exists, a fetch-and-classify
pass) on every one of them; assigning SFO or MFO without evidence to support it would have been
fabrication, so these are labelled `Subtype unconfirmed` rather than guessed.

**A caveat on this table's own sourcing, stated up front because the instruction was to be exact
about it:** the bounded 1-hop crawl's per-record results file (`pass_b_results.json`) was deleted
after its findings were applied to the CSV in an earlier pass — a real gap, not a hidden one.
Where a record's own `blind_spots`/`classification_evidence` field or `DECISIONS.md` documents
the specific resolution outcome, that's what's used below. Where it doesn't, the table says
**"reason not recorded in logs"** rather than reconstructing the outcome from memory of a file
that no longer exists.

| Firm | How it qualified | Resolution attempted | Why subtype is unresolved | Source |
|---|---|---|---|---|
| Destiny Family Office | Class D — first-party website self-description (legal name + founder-bio industry description) | Fetched 3 pages at the firm's own site; separately, the founder's bio was read directly | Prose present, but describes the founder's group of businesses ("two independent RIAs, a multi-family office, multiple wealth management firms") without cleanly naming which entity in that group the "multi-family office" phrase refers to | https://www.Destinyfamilyoffice.com |
| Jarrow Capital | Class A — Wikidata P31/P279* = Q751314 | Website matched (on file, not guessed); re-fetch attempted | Fetch failed — the specific failure mode is not recorded in this record's log | https://www.jarrowcapital.com/ |
| Revisio Family Office | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | https://revisio-family.de |
| Redwood Holdings | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | https://www.redwoodholdings.net/ |
| Bancard Group | Class A — Wikidata P31/P279* = Q751314 | Domain guesses tried (bancard.com/.net/.org), none matched; web-search entity resolution also returned none | No website exists or could be resolved | n/a — no website disclosed or resolved |
| Prime Opportunities Investment Group | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | http://www.primeopp.com/ |
| 166 2nd Financial Services | Class A — Wikidata P31/P279* = Q751314 | Domain guesses tried (3 variants), none matched; web-search entity resolution also returned none | No website exists or could be resolved | n/a — no website disclosed or resolved |
| Korys | Class A — Wikidata P31/P279* = Q751314 | 3 pages fetched (only `hq_country` was extractable) | Prose crawled but contained no firm-anchored single/multi-family subtype language | https://www.korys.be/ |
| Diethelm Keller Holding | Class A — Wikidata P31/P279* = Q751314 | Domain guesses tried (3 variants), none matched; web-search entity resolution also returned none | No website exists or could be resolved | n/a — no website disclosed or resolved |
| Fundus Heritage Ventures | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | https://fundusheritage.com |
| Blanck Capital | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | https://blanckcapital.com/ |
| Fundus Heritage | Class A — Wikidata P31/P279* = Q751314 | Domain guess run; 1 page fetched | No extractable/evidence-supported content found on the page | https://fundusheritage.com/ |
| Rahul Guhathakurta HUF Office | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched (description, firm_email, hq_state were extractable) | Descriptive prose was found and used for other fields, but contained no firm-anchored single/multi-family subtype language | https://www.rghuf.com |
| Builders Vision | Class A — Wikidata P31/P279* = Q751314 | 2 pages fetched | No extractable/evidence-supported content found on either page | https://www.buildersvision.com/ |
| DFO Management | Class A — Wikidata P31/P279* = Q751314 | 1 page fetched | No extractable/evidence-supported content found on the page | https://www.dellfamilyoffice.com/ |
| Jake P. Noch Family Office, LLC | Class A — Wikidata structured facts beyond name (founder, HQ, website), treated as equivalent to A | A website is on file | **Reason not recorded in logs** — no fetch/crawl outcome for this record's own website is captured anywhere in its log, despite a website existing | https://www.jakepnoch.com/ (untested per available logs) |
| TriEdge Investments | Class A — Wikidata P452 = Q751314 | Bounded 1-hop crawl found a team-page bio containing "multi-family office" | Prose present, but it describes an employee's **prior employer**, not TriEdge itself — correctly rejected by the bio-transition guard (see `DECISIONS.md`, "Bio-transition guard reinstated") | https://www.triedgeinvestments.com/team |

**Tally by reason** (using the actual reasons recorded above, not forced into a fixed category
list where the specific mechanism wasn't logged):
- No website exists or could be resolved: 3 (Bancard Group, 166 2nd Financial Services, Diethelm
  Keller Holding)
- No extractable/evidence-supported content found on a fetched page: 8 (Revisio, Redwood, Prime
  Opportunities, Fundus Heritage Ventures, Blanck Capital, Fundus Heritage, Builders Vision, DFO
  Management)
- Prose present but not firm-anchored to the subject firm's own subtype: 4 (Destiny, Korys, Rahul
  Guhathakurta HUF Office, TriEdge)
- Fetch failed, specific mechanism not recorded: 1 (Jarrow Capital)
- Reason not recorded in logs at all: 1 (Jake P. Noch Family Office, LLC)

3 + 8 + 4 + 1 + 1 = **17.**

Note what this tally does *not* contain: no row above cites `robots.txt` or a DNS failure as the
specific reason, even though both were true of *some* records crawled during this project's
bounded 1-hop pass. Neither mechanism is stated in this record's own persisted log, and the
per-record file that would have confirmed it no longer exists — so neither is claimed here.

## Material blind spots

- **`firm_email` is 11/50.** Item 1.J/1.K on the ADV filing itself was blank for every candidate
  checked — the populated addresses came from a separate contact-page pass (homepage,
  `/contact`, `/contact-us`, `/about`) run against resolved websites, restricted to generic
  role mailboxes (`info@`, `admin@`, `team@`, `inquiries@`) on the firm's own domain and passed
  through MX validation, plus a later targeted enrichment pass on the 4 SFO records specifically.
  Personal/named mailboxes and off-domain matches found in these passes were logged but not
  populated into this field — see `pilot_contact_audit_log.csv`. No address was constructed.
- **SFOs are 4/50** — a minority despite this project's own SFO-plausible ceiling (HNW ≤ 5)
  existing in the classifier, for the exemption reason above. 2 are ADV-sourced (registered
  despite the exemption existing); 2 are Wikidata-sourced (Mayfair, via its own homepage
  self-description; Paulson & Co., via a manual reading of its Wikipedia article — see the
  disclosed exception above).
- **16 records rest on Class C alone**, the weakest evidence tier.
- **Retrieval is lexical, not semantic** — TF-IDF, not embeddings. Adequate at 50 records, the
  binding limitation at 5,000.
- **Geographic concentration is US-heavy** because every high-yield channel is a US regulatory
  disclosure. Item 5.D has no equivalent in Switzerland, Singapore, or the UK — Switzerland alone
  has the world's highest millionaire density and a correspondingly dense family-office market,
  none of it reachable by filing-based methods. Wikidata supplied the only non-US records. Closing
  this needs jurisdiction-specific registry connectors and a classification method not dependent on
  US-style client-type disclosure.
- **ProPublica officer/address bridge not built:** the API returns aggregate financials; the officer
  schedule exists only on the filing PDF, and a PDF table extractor was out of budget.
- **Sector and thesis data largely absent**, so sector queries correctly return nothing.
- **Search-backend availability** is an external dependency outside the system's control, as
  Finding 3 demonstrated.
