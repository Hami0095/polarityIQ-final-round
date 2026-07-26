# Build Session Summary

**Approximate working time:** ~16+ hours across 5+ sessions inside the 48-hour window (first
commit 2026-07-25 16:07 through further work after the 2026-07-26 19:02 freeze — bio-transition
guard fix, targeted SFO-record enrichment, 13F holdings deltas, a terminology-expansion cycle,
and full documentation reconciliation — with real gaps between sessions, not continuous effort).
The hour figure is inferred from session content and `DECISIONS.md` entry density, not a
timesheet — I don't have precise instrumentation of active-vs-idle time, and I'd rather say so
than imply false precision.

**Sessions.**
- **Session 1 (~2 hrs)** — Environment constraints confirmed, discovery channels built (Form ADV
  bulk, 13F index, ProPublica 990), schema (`SourcedField`, `Firm`, evidence tracking) laid down,
  first 9-firm pilot batch assembled.
- **Session 2 (~3 hrs)** — Enrichment pass, then the provenance audit: found the pilot batch had
  actually been hand-researched into Python literals rather than produced by running code, and
  rebuilt the enrichment layer (`fetch → extract → validate`) so discovery, fetching, extraction,
  and classification all execute inside the program. LLM extraction wired to a local Ollama
  instance after testing two models against a known-answer page. Website domain-guess resolution
  built, with a real false positive (`pointone.com`, an unrelated company) caught and fixed.
- **Session 3 (~4 hrs)** — Classification module built (affirmative-evidence-only, never from
  name), entity-type filtering, a skeleton RAG deployed to a real public URL, then a full pipeline
  run that surfaced a rate-limit incident and a zero-yield evidence-gate bug, both fixed. Real RAG
  (TF-IDF retrieval, gated synthesis) built and redeployed; dataset locked at 28 with the
  evidence-class architecture (A/C/D tiers) in place.
- **Session 4 (~7 hrs, the longest)** — Self-audit found a 20% classification error rate on a
  five-record sample, then a full audit of all fifteen phrase-classified records; the
  source-concentration cap found to have been silently bypassed by ad hoc CSV writes and fixed;
  expansion from 28 to 50 records across several rounds of Wikidata broadening and 13F
  cross-referencing; a second false-positive shape (TriEdge) found after the anchor rule
  mistakenly replaced a guard it wasn't actually a superset of, reinstated with a regression test;
  the RAG app's own header text found stuck at "28 records" through five expansions and fixed to
  read the live count; the five write-up deliverables produced and reconciled against the CSV.
- **Session 5 (post-freeze)** — Bio-transition guard reinstated after the TriEdge false positive
  exposed a collapsed-check gap; a targeted enrichment pass on the 4 SFO records specifically for
  `firm_email`; 13F holdings deltas reconciled; a terminology-expansion cycle; final documentation
  reconciliation across all deliverables (final state: 29 MFO / 4 SFO / 17 subtype unconfirmed,
  `firm_email` 11/50).

**What the AI produced vs. what I decided.** Claude Code wrote most of the implementation —
connectors, parsers, the classifier, the RAG. My contribution was the decisions it couldn't make
and the checks it didn't think to run: auditing whether the pipeline actually produced the
dataset (it didn't, and the enrichment layer was rebuilt); demoting Form D after testing showed
74% fund vehicles; refusing to relabel firms to improve the SFO count; sampling my own records
the way a reviewer would, which found a 20% error rate in website-phrase classification; setting
and then honestly recalibrating the source-concentration cap; and stopping at 50 rather than
breaching it for a rounder number.

Several fixes came from disbelieving a result rather than accepting it — clustered search
rejections that turned out to be a blocked backend, a 0% extraction yield that turned out to be
my own gate rejecting prose, and a suspiciously clean classification that turned out to be a
contact-form dropdown.

**What's still open, honestly:** field-level benchmark agreement against the ground-truth fixture
did not complete — it requires a full live re-enrichment run that timed out; only the fast, local
discovery-recall comparison ran (7/15). `firm_email` coverage is 11/50. Retrieval is lexical, not
semantic, by explicit choice at this corpus size.
