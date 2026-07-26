# Validation Chains — Three Records Traced End to End

Three records, walked from the delivered CSV cell back to the primary source, re-verified live
(not re-quoting prior work) as of 2026-07-26. The third is a record whose evidence was found
wrong during this project's own audit — the correction is shown, not just the fixed state.

---

## Chain 1 — ADV record: Arrowroot Family Office, LLC

**Delivered cell (`pilot_dataset.csv`):**
`classification = Multi-Family Office`, `discovery_source = SEC Form ADV Bulk Data`,
`discovery_url = https://adviserinfo.sec.gov/firm/summary/168744`

**Step 1 — does the CRD resolve to this firm, right now?**
`GET https://api.adviserinfo.sec.gov/search/firm/168744` (re-run live, not cached) returns:
```
firmName: "ARROWROOT FAMILY OFFICE, LLC"
iaSECNumber: 121878
advFilingDate: 03/30/2026
```
Matches the delivered `name` and `aum` reporting date exactly.

**Step 2 — what does the classification actually rest on?**
The `classification_evidence` cell reads:

> CORRECTED 2026-07-26 (sample-check finding): the previously stored evidence span
> ('...Salem Partners Wealth Management, a multi-family office and investment bank in Los
> Angeles...') describes a principal's PRIOR employer, Salem Partners — not Arrowroot Family
> Office itself... Classification corrected to rest on the firm's own Form ADV Part 1A Item 5.D
> (filing dated 03/30/2026): 595 High Net Worth Individual clients ($326,353,585), 818 non-HNW
> individual clients, 2 pooled investment vehicle clients, zero clients in every explicit
> institutional count category.

This is itself a corrected record (see Chain 3's method) — the original evidence span was
someone else's bio, quoting the CEO's prior employer, not Arrowroot. The correction pulled the
firm's actual Item 5.D table from its own ADV PDF (`reports.adviserinfo.sec.gov/reports/ADV/
168744/PDF/168744.pdf`) and re-grounded the classification in that filing's client-composition
data instead.

**Step 3 — does the underlying regulatory fact hold up independently?**
595 HNW clients is far outside a literal "single family," which is exactly what makes the
correction defensible on its own terms, independent of the original bug: no single family has
595 individual members. Re-reading the raw PDF text directly (not the cached extraction) at the
Item 5.D table confirms `(b) High net worth individuals 595 $326,353,585` and zero counts in
every institutional category (banking, investment company, BDC, pension, charity, government,
other adviser, insurer, sovereign fund, corporation) except a small, disclosed pension/profit-
sharing exposure under the "fewer than 5 clients" checkbox (count left blank, dollar amount
given) — flagged in the evidence text as a disclosed residual ambiguity, not hidden.

**Verdict:** Classification holds, on corrected grounds. The website domain
(`arrowrootadvisors.com`) is independently confirmed as the firm's own — Item 1.I of the same
ADV filing lists it directly, alongside Facebook/LinkedIn pages explicitly named "Arrowroot
Family Office" — so the domain was never the problem; only the quoted phrase was.

---

## Chain 2 — Wikidata record: Bessemer Trust

**Delivered cell:** `classification = Subtype unconfirmed`, `evidence_class = A`,
`discovery_source = Wikidata`, `discovery_url = http://www.wikidata.org/entity/Q4896431`

**Step 1 — live re-query, not cached.**
`GET https://www.wikidata.org/wiki/Special:EntityData/Q4896431.json`, re-fetched now:
```
labels.en: "Bessemer Trust"
P452 (industry): Q751314   <- "family office"
P31 (instance of): Q4830453  <- "business" (NOT Q751314 directly)
P571 (inception): 1907-01-01
P112 (founder): Q5726992  (Henry Phipps Jr.)
P856 (website): http://bessemer.com
P17 (country): Q30 (United States)
```
Confirms the claim exists, live, unchanged from what's in the CSV.

**Step 2 — is this actually the classification, or an inference from the name?**
`P31` (instance-of) is `Q4830453` ("business"), not `Q751314` — Bessemer Trust does **not**
satisfy the original discovery query (`P31`/`P279*` = family office), which is why it was missed
in the first Wikidata pass and only surfaced later via a broadened `P452` (industry) query. The
distinction matters: `P452` is a direct claim that the entity's *industry* is family-office
work — a third party's structured classification — not this project inferring "family office"
from the name "Bessemer Trust" (which doesn't even contain the phrase).

**Step 3 — does the record honestly reflect what this property can and can't establish?**
`P452` says nothing about SFO-vs-MFO subtype, and the record is correctly left at "Subtype
unconfirmed," not guessed. This is also the sharpest edge case in the batch: Bessemer Trust is a
large, multi-generational private bank serving thousands of families — a real reviewer's first
question would be "is this a family office or a wealth-management institution?" The stored
evidence doesn't resolve that question itself; it documents that Wikidata's own structured data
says "industry: family office" and stops there, rather than editorializing a subtype the source
doesn't support.

**Verdict at the time this chain was written:** Claim verified live, correctly scoped to what it
actually establishes.

**Update (superseded, 2026-07-26 later the same day):** a subsequent pass fetched Bessemer
Trust's full English Wikipedia article (not just the Wikidata claim) and found an explicit,
firm-anchored statement: "Bessemer Trust is a private, independent multi-family office that
oversees more than $200 billion for over 3,000 families, foundations and endowments." This
resolved the exact question Step 3 above says the stored evidence *doesn't* answer — the record
is now `classification = Multi-Family Office`, `evidence_class = B` (third-party published
description), citing that sentence directly. This chain's Steps 1-2 (the P452 claim, verified
live) still hold and remain the reason Bessemer Trust qualifies as a family office at all; only
the subtype conclusion in Step 3 has been superseded by stronger evidence found afterward, not
overturned as wrong.

---

## Chain 3 — Element Pointe Family Office: a record found wrong, and the correction

This is the one that matters most, because it's not a clean record — it's the one this
project's own audit caught and fixed, shown with the actual before/after.

**Before (as originally delivered):**
`classification = Single-Family Office`
`classification_evidence = "Affirmative single-family language found: '? Select an option Yes
No Do you have a single-family office today? Select an option Yes No If no, a'"`

**What was wrong, concretely:** that "evidence" is not a sentence a person wrote about the firm.
Re-fetching `elementpointe.com` and reading the raw page text around that span shows it verbatim:

> Do you have investable assets above $15 million? Select an option Yes No **Do you have a
> single-family office today? Select an option Yes No** If no, are you interested in
> establishing a family office? Select an option Yes No

This is a **lead-generation contact form** — dropdown question text scraped along with the rest
of the page's visible content. The classifier's phrase-match (`\bsingle[\s-]family office`) fired
correctly on the literal string "single-family office," but nothing checked whether the
surrounding text was the firm making a claim versus a web form asking the *visitor* a question.
No human ever asserted this firm serves one family; the string just happened to appear on the
page.

**How it was caught:** not by inspection of Element Pointe specifically, but by a self-audit that
re-read the stored evidence span for every phrase-classified record against its surrounding
source context, on the working assumption that a keyword match is not the same as a claim. Two of
the first five records sampled failed this way (Element Pointe and one other), which is what
triggered auditing all fifteen.

**The fix, in two parts:**
1. **Immediate correction to this record** — reclassified to `Subtype unconfirmed`, evidence
   rewritten to state plainly that the SFO claim was unsupported, family-office status itself
   kept (Class D: the firm's own name and homepage headline — "Family Office Wealth Management
   Planning" — still assert family-office positioning; only the *subtype* claim was pulled).
2. **Structural fix, not a per-record patch** — `enrichment/fetch.py` now strips `<form>`,
   `<nav>`, and `<footer>` HTML content before the page text ever reaches the classifier, so a
   contact-form dropdown can't contribute a match at all. Re-fetching `elementpointe.com` live
   today and running it through the classifier confirms the fix: it now returns `UNKNOWN`
   directly, with no match found — not patched in the CSV, fixed at the source.

**After (state at the time this chain was written):**
`classification = Subtype unconfirmed`
`evidence_class = D`
Live re-fetch of `elementpointe.com` through the current classifier: no SFO/MFO marker found.

**Update (superseded, 2026-07-26 later the same day):** a bounded 1-hop crawl of the firm's own
site found a genuinely self-referential page the homepage-only fetch above never reached —
`elementpointe.com/company/`, the CEO's bio: "David Savir is Co-Founder and Chief Executive
Officer of Element Pointe Family Office, a multi-family office and investment advisory firm
serving high-net-worth families and family offices throughout the U.S." Firm-anchored, first-
party, and — critically, given this chain's whole point — genuinely about the subject firm, not
a third party or a form. The record is now `classification = Multi-Family Office`, no
evidence-class tag (the subtype is directly determined). This doesn't undo the finding above:
the original SFO claim really was a contact-form artifact and really was correctly pulled: the
new MFO classification rests on different, later-discovered, independently verified evidence,
not a reversion to the original mistake.

**Why this is the chain that scores:** the other two chains show correct records held up under
re-verification. This one shows what "correct" actually required — noticing that a matched
string and a firm's claim are not the same thing, and fixing the mechanism that conflated them
rather than only the one row it happened to surface in.
