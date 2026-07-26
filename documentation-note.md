# Documentation Note — Micro-RAG System

I'm writing this the way I'd actually explain the system to someone about to poke at it, not the
way a spec sheet would. Where something is a genuine tradeoff rather than a clean win, I've tried
to say so.

## Stack, briefly

Deployment is a single standalone Python function on Vercel — no framework, one handler.
Retrieval is TF-IDF with cosine similarity, built from scratch, no scikit-learn, no numpy. Fuzzy
fallback uses `rapidfuzz`, which was already a dependency elsewhere in the project for entity
resolution, so it didn't add anything new. Synthesis is template assembly over fields that have
already cleared an evidence gate — there's no LLM call at serve time. Live at
https://ragapp-sand.vercel.app.

### Why not embeddings

Honestly, the corpus is small enough that it barely matters, and that's worth saying plainly
instead of dressing it up as a design philosophy. Fifty documents fit in memory with room to
spare, and a transformer runtime in a serverless function adds cold-start latency and real risk
against Vercel's size limits, for a corpus where the payoff wouldn't show up anyway.

But I don't want to pretend TF-IDF is doing something it isn't. It's lexical — matching term
overlap, not meaning. Query 3 in the live log ("family office focused on impact and
mission-driven investing") returns firms whose descriptions happen to share *words* with the
query, not necessarily the firms whose actual strategy matches the concept. At fifty records with
short descriptions, the gap between "shares words" and "means the same thing" rarely shows. At
five thousand it would be the main limitation, and embeddings would be the first thing I'd
reach for.

### Why not an LLM at serve time

The extraction pipeline talks to a local Ollama instance that isn't internet-exposed, so the
deployed function simply has no model to call even if it wanted one. I could treat that as a
constraint to work around. Instead synthesis is template assembly over fields that already
passed the evidence gate upstream — nothing is generated freely at serve time, full stop.

That turned out to matter more than I expected going in. Query 14 in the log asks the system to
assert a $5B AUM figure for a firm that has no such figure on file. There's no generation step
for that instruction to bend — the sentence is just tokenized as a bag of words, the same as any
other query. The system isn't declining because it was told to; there's no mechanism by which it
could comply even if it "wanted" to. That's a stronger property than a prompt-level instruction
not to fabricate, and it wasn't really the plan going in — it fell out of the no-LLM-at-serve-time
decision almost by accident.

## Chunking — or rather, the lack of it

There's no chunking. Each firm is one document, and the corpus is fifty documents total.

Chunking solves two problems — fitting long documents into an embedding context window, and
improving retrieval granularity over documents long enough that a query might only be about one
section of one. Neither problem exists here: these are structured records averaging a few hundred
characters, and splitting one across chunks would just fragment the exact thing a user is trying
to find. I'm calling this out as a deliberate choice, not an oversight, mostly because "no
chunking" can look like a step someone forgot rather than a step that doesn't apply.

Searchable text per document is: firm name, classification, HQ city/state/country, description,
principal names — plus a US state name↔abbreviation expansion, since a query for "California"
needs to match records that store `CA`. That expansion exists because of a real bug found during
testing, described below.

Two token classes get stripped before either documents or queries are vectorized:
**domain-universal stopwords** ("family", "office", "offices" — present in nearly every document
here, since every record is some kind of family office) and, since a later pass, **general
English stopwords** (prepositions, articles, common verbs like "is"/"are"/"has"). Both removals
came from the same root problem, described under *what didn't work*, and the second one only got
added because the first fix, on its own, turned out to be a partial version of the same bug.

## Retrieval, step by step

1. Structured filters (classification, state) apply first — exact match, not scored.
2. TF-IDF cosine similarity runs over whatever's left.
3. Results above a nonzero-score floor come back, capped at ten.
4. Zero results triggers a fuzzy match against firm names. If something's close, the system
   returns a **suggestion** — it never silently substitutes the corrected query and runs it. The
   user sees "did you mean X," not results for a query they didn't type.
5. Every field on every result still has to clear the evidence gate before it's rendered, no
   matter how it got selected.

## The grounding control

This is the same code as the enrichment pipeline's gate, not a second, parallel mechanism
invented for the demo. `GroundedField.evidence_supports_value()` requires a field's value to be a
literal substring of its stored evidence span, and that span itself has to be a literal substring
of the document that was actually fetched. Fail either check and the field doesn't render — it
shows up under "Insufficient evidence for: ..." in the answer instead of just quietly vanishing.

It's a duplicated copy rather than an import, because the Vercel function deploys standalone
without the rest of the repo bundled in. I'd call that a real cost, not a stylistic choice — two
copies of the same logic is exactly the kind of thing that drifts apart over time if nobody's
watching. Right now they're identical by construction; if they ever diverge, that's a bug to go
fix, not a difference to explain away.

**Why the two-part check exists at all, specifically:** during extraction testing, one model
(`minimax-m3:cloud`) returned a fabricated AUM figure *along with* a fabricated evidence span to
match it — meaning a single check (is the value present in its own span?) would have sailed
straight through, because the model had helpfully supplied both halves of the lie. The second
check — is the span itself present in the actual fetched document? — is what closes that hole.
The same two-part gate now governs what this deployed system is allowed to tell a user, for the
same reason. A control built against something that actually happened is worth more than one
built against something I imagined might happen, and this is a case where I have the incident to
point to rather than just the intuition.

For a more granular version of that same idea — not "the gate works in general" but "here's one
specific record where the underlying evidence was wrong, and here's what fixed it" — see the
validation-chains write-up from Task 1. One of the three chains there walks a record
(Element Pointe) whose stored evidence turned out to be a contact-form dropdown, not a claim
anyone made, and shows both the individual correction and the structural fix that followed it.
That's the same "gate" idea, just demonstrated on a record that actually failed it once, rather
than asserted about the system as a whole.

## What actually works

- **Exact and near-exact name lookup.** Query 2 returns exactly one result for "Arrowroot Family
  Office" now. Before the stopword fix it returned ten results, nine of which were noise.
- **Structured filters.** Queries 4 and 5 — no classification leakage anywhere in the log.
- **Typo tolerance that doesn't guess.** Query 7, "arowroot," returns zero results plus an
  explicit suggestion at score 78.8. The suggestion only fills the search box; it never runs the
  corrected query on its own. The system doesn't get to decide what you probably meant.
- **Honest declines.** Queries 8, 9, and 11 return zero results with an explicit message, not
  keyword-matched filler dressed up as an answer.
- **Field-level declines.** Query 13 returns Korys with `firm_email` explicitly listed as
  insufficient evidence — no fabricated contact data shows up anywhere in the log.
- **Mixed queries.** Query 15 answers HQ and AUM with citations while declining email in the same
  response, rather than either refusing the whole thing or fabricating the missing piece.
- **Resistance to a leading question.** Query 14, described above.

## What genuinely doesn't work

Worth naming plainly, because a system this size has real limits and there's no point being
precious about them.

- **Retrieval is lexical, not semantic**, as already covered. "Impact investing" only matches
  firms whose text literally contains those words; a conceptually similar firm described
  differently is invisible to this system.
- **Sector and thesis data is largely absent**, so sector-specific queries correctly return
  nothing rather than approximating an answer nobody asked for.
- **An empty query returns dataset-order rows with `status: success`**, which is shaped exactly
  like a real result set even though it isn't answering anything. Every field is still gated, so
  nothing false gets through — but a user could reasonably misread this as a match.
- **The result cap is a flat ten, no pagination.**
- **`Subtype unconfirmed` is honest, but it's not the same as a resolved answer.** 17 of 50
  records carry it — firms confirmed as family offices (via Wikidata's own structured claim, or
  first-party self-description, or Form ADV client-structure data) whose single-vs-multi status
  genuinely couldn't be pinned down from what's available. That's a real gap for a user who wants
  a definite answer, even though the alternative — guessing — would be worse.

## The live query log

Fifteen queries, run with `requests.get()` straight against the production URL, not localhost —
covering success cases, graceful degradation, and outright declines. Verbatim requests, unedited
responses, and a per-query assessment live in `docs/live_queries.md`; the raw JSON is in
`data/interim/live_queries_raw_50.json`.

There are actually several generations of that log — against 28-, 40-, and 50-record versions of
the dataset as it grew. I kept the earlier runs rather than editing them down, including the ones
that recorded real failures later fixed, because a log that only ever shows the system succeeding
isn't really a log.

### Two things the log itself found, and what each one taught me

**First: domain-universal tokens were quietly defeating the retriever.** Query 8, "family offices
in Japan," came back with ten US firms and `status: success`. Not one firm in the corpus is
Japan-based.

My first instinct was a minimum score threshold, and it's worth saying why that wouldn't have
worked rather than just asserting it doesn't. "Family" and "office" show up in nearly every
document in this corpus, so a query that's pure noise except for those two words was scoring
*higher* than a real, narrow, meaningful query — a threshold would have had to reject the
higher-scoring noise while keeping the lower-scoring signal, which isn't really something a single
cutoff number can do. The actual fix was removing those tokens from the index entirely, for both
documents and queries. Queries 8 and 11 now decline correctly, and query 2 got noticeably more
precise as a side effect — ten results down to one.

**Second: fixing that exposed a bug the noise had been hiding the whole time.** With the dominant
tokens gone, query 5 ("family office California") dropped to zero results. It turned out `hq_state`
is stored as `CA`, and the literal word "California" had never matched anything, ever — the
"family"/"office" noise had just been returning ten results regardless, which looked like success
and wasn't. Fixed with a state name↔abbreviation map; query 5 now returns three genuinely
California-based firms.

I think the general lesson here is more interesting than either bug on its own: the first fix
didn't create the second bug, it revealed one that had been there the entire time. A retrieval
system that returns plausible-looking results is not the same thing as one returning correct
results, and noise in a scoring function can hide a real defect indefinitely — you only find it
once you take the noise away.

**A third thing, smaller but worth including:** turning on `aum` in the rendered fields
immediately surfaced a record showing `$0&nbsp;Billion` — a broken extraction artifact, literal
HTML entity and all, that had been sitting in the CSV the entire build because nothing ever
displayed it. Nulled before the log was finalized. The lesson generalizes past this one field: a
value you don't surface is a value you're not actually validating, no matter how confident the
pipeline felt about it at write time.

## Where I'd put the next hours, in order

1. **Contact intelligence.** `firm_email` coverage is thin relative to the rest of the file. A
   contact-page pass across resolved websites — homepage, `/contact`, `/about` — for published,
   verifiable office addresses is the obvious next step, and it's already partly done; more of
   the corpus could still benefit from it.
2. **Neural embeddings**, once the corpus is large enough that lexical matching starts missing
   real conceptual matches often enough to notice.
3. **Sector and thesis extraction**, which would make the semantic-sounding queries this interface
   already invites actually answerable instead of correctly-but-unsatisfyingly empty.
4. **Explicit per-field declines for structurally absent data.** If a user asks about sectors and
   the field is empty across the whole corpus, saying so directly beats a bare zero-result
   response that looks like every other kind of miss.
5. **Import the gate instead of duplicating it.** A shared package would remove the divergence
   risk the current copy-paste carries, even if the two copies happen to agree today.
6. **Pagination, and some visible signal about how many results exist beyond the cap.**
