Context

I'm building a small, production-shaped system for a technical assessment. It has two
deliverables built on one foundation:


A dataset of 50 real, verified family office records (firms + principal contacts + recent
signals), produced by an AI-driven pipeline — not manually assembled.
A Micro-RAG application deployed to a public URL that lets a non-technical user query that
dataset in natural language, with a real grounding control (not just a system prompt) that
makes the app qualify or decline answers when the underlying data doesn't support them.


The dataset is the actual product being evaluated. The RAG app is the delivery layer. Do not
let architectural polish on the RAG side substitute for rigor on the data side.

Hard constraints — do not violate these


Multi-source discovery, not one convenient source. Design discovery so firms are found
through several independent channels (e.g. SEC ADV/Form D filings, state UHNW/family-office
directories, press/deal databases, LinkedIn company search, conference speaker/sponsor lists,
philanthropic foundation filings/990s). Log which source found each firm. If one source
contributes more than ~30-40% of the final 50, flag it to me before finalizing — that's the
single most common failure mode in this assessment.
Two separate rules of proof, don't conflate them:

Cell-level: every high-value field (contact email/phone, AUM, thesis, etc.) must carry
its source + how it was confirmed. If it can't be verified, leave it blank and label it
"could not verify" — never guess-and-label-as-verified.
Firm-level: a firm only qualifies as a "family office" record with affirmative evidence
(filings, first-party description, credible secondary source describing it as serving one
family's or a small number of families' wealth) — not just because it has "family" in the
name or appears in a family-office-adjacent list. Classify each as Single-Family Office,
Multi-Family Office, or Unable to Determine. Never relabel a wealth manager or MFO as an SFO
to make the file look more valuable.



Contact data honesty. Never fabricate or infer a personal email/phone number and present
it as verified. Only include contact fields that trace to something checkable (a company
"team" page, a filing, a public LinkedIn profile, a press mention) and note the check you ran
(e.g. an email-deliverability/syntax check, a cross-reference against a second source). If a
validator flags an address as undeliverable, it must not appear in the delivered contact
field — move it to an audit/rejected log instead.
The 50 = 50 qualifying records, not 50 rows. Build in a de-dup and inclusion-standard
filter so duplicates, unconfirmed-type firms, and records that fail the firm-level rule above
don't count toward the 50.
Prefer single-family offices where discoverable — they're the harder, more valuable find.
Don't let the pipeline default to easy-to-find multi-family offices and advisory firms.


Schema (adapt freely, this is a reference shape, not a copy requirement)

Firm level: name, description, investment thesis, sectors/mandate, AUM (with source), HQ
address/city/state/country, domain, website, corporate LinkedIn, classification
(SFO/MFO/Unable to Determine) + evidence for that classification.

Principal level: first/last/full name, title, LinkedIn, work email, direct phone — each with
source + verification method, or honestly blank.

Signal level: recent investments, fund commitments, key hires, news — each dated and sourced.

Add a confidence and sources column pair for every high-value field, plus a per-record
blind_spots note (what you looked for and couldn't confirm).

What to build, in order


Repo scaffold — Python project, real git history (no squashing), clear module boundaries:
discovery/, enrichment/, validation/, dataset/, rag/, app/. A DECISIONS.md file
where you (Claude Code) log, as you go, what you chose to prioritize, what you're uncertain
about, and why — this is graded content, keep it honest and specific, not polished.
Discovery layer — scripts/agents that query multiple source classes above and output a
candidate list with discovery_source per firm. Dedup by domain/name fuzzy-match.
Enrichment layer — per-candidate lookups to fill firm + principal + signal fields, each
write tagged with its source.
Validation layer — a real, running check for each high-value field type (e.g. email
syntax + MX/deliverability check, phone format/region check, cross-source corroboration for
AUM/thesis claims). Output a validation log per record, and enforce it — failed cells get
nulled/blanked in the delivered dataset, not just flagged.
Dataset assembly — apply the firm-level qualifying filter, cut to the final 50, write
CSV/XLSX, and auto-generate the methodology summary (sources used for discovery vs.
verification, blind spots) from the actual run logs — don't hand-write a summary that doesn't
match what the code did.
Full validation chain export for 3 records I'll select later — discovery source,
extraction method, enrichment steps, validation logic, confidence, exact links.
Micro-RAG app — ingest the dataset, chunk it sensibly (separate structured filters from
semantic text so numeric/categorical queries don't rely on embedding similarity), build
retrieval + generation with a grounding control that:

only lets the model state what retrieved records support,
explicitly declines/qualifies when retrieval confidence or coverage is low,
is enforced in code (e.g. citation-checking or constrained retrieval-then-template), not
just instructed via prompt.
Build a clean, non-technical UI (a fund-manager persona should be able to use it with zero
context) — not a JSON/dev console. Handle empty/partial/failed queries with readable
responses, not error dumps.



Deploy to a real public URL (Vercel/Render/Fly/Railway free tier, or similar).
Docs — stack choices, chunking strategy, embedding model, retrieval approach, actual
live queries you (Claude Code) ran against the deployed system and what they returned, what
doesn't work yet, what you'd improve next.


Testing requirement

Before calling this done: run real queries against the deployed app (not just local), and
record the actual outputs in the docs. Distinguish "the record is wrong" failures from "the
answer misstates a correct record" failures — the assessment explicitly grades both layers
separately.

Working style

Be transparent in DECISIONS.md about tradeoffs, what you skipped and why, and anything you're
not confident is right. Don't pad scope with extra "impressive" features (extra agents, extra
dashboards) that don't improve dataset trustworthiness or answer grounding — depth over
breadth. Stop and ask me if a design decision has real cost/legal implications (e.g. which paid
API to use, whether to scrape a site with restrictive terms of service).