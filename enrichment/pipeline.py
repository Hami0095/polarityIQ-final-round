"""Dispatch a DiscoveryRecord to the right enrichment path by discovery_source,
then run a second pass that guesses and verifies each firm's own website and
fills whatever fields the deterministic source couldn't (description, thesis,
sectors, aum, additional contact) via LLM extraction, then classify.

Pipeline order, each step a real gate rather than a formality:
  1. entity_filter.check_entity_type() on the raw candidate name — a pooled fund vehicle,
     asset manager, or bank/trust/law firm is rejected here and never even gets enriched.
     Built after the 2026-07-25 EDGAR viability check found 74% of EDGAR's "family office"
     Form D matches were exactly this shape.
  2. Deterministic parsing (EDGAR Form D, ProPublica 990) — reliably structured sources
     shouldn't go through the LLM path (Correction 1).
  3. Website guess-and-verify + LLM extraction, filling only fields the deterministic source
     left blank.
  4. classification.classify() against whatever source text is available. No affirmative
     evidence -> Unable to Determine, which does not count toward the qualifying set.
"""
from __future__ import annotations

from dataclasses import dataclass

from dataset.classification import classify
from dataset.entity_filter import check_entity_type
from dataset.schema import Classification, DiscoveryRecord, Firm
from discovery.store import load_candidates
from enrichment.adv_enrich import enrich_adv_candidate
from enrichment.edgar_13f_enrich import enrich_13f_candidate
from enrichment.edgar_enrich import enrich_edgar_candidate
from enrichment.propublica_enrich import enrich_propublica_candidate
from enrichment.sec_submissions import enrich_from_submissions, extract_cik
from enrichment.website_resolve import enrich_website_for_firm
from enrichment.wikidata_enrich import enrich_wikidata_candidate
from discovery.websearch import enrich_candidate_via_search

DETERMINISTIC_ENRICHERS = {
    "SEC EDGAR Form D": enrich_edgar_candidate,
    "ProPublica Nonprofit Explorer (990)": enrich_propublica_candidate,
    "SEC Form ADV Bulk Data": enrich_adv_candidate,
    "Wikidata": enrich_wikidata_candidate,
    "SEC EDGAR 13F Filer List": enrich_13f_candidate,
}


@dataclass
class RejectedCandidate:
    name: str
    discovery_source: str
    discovery_url: str | None
    reason: str
    evidence_span: str | None


def enrich_candidate(record: DiscoveryRecord) -> Firm | None:
    enricher = DETERMINISTIC_ENRICHERS.get(record.discovery_source)
    if enricher is None:
        return None  # no deterministic path for this source yet
    return enricher(record)


def _classification_source_text(firm: Firm) -> str:
    """Everything available to classify from EXCEPT the firm name — classifying from the
    name alone (e.g. a family surname) is the exact mistake this pipeline exists to avoid."""
    parts = [firm.description.value, firm.investment_thesis.value, firm.blind_spots]
    return " ".join(p for p in parts if p)


def run_enrichment(
    resolve_websites: bool = True, use_websearch_fallback: bool = True,
) -> tuple[list[Firm], list[DiscoveryRecord], list[RejectedCandidate]]:
    """Returns (qualifying_firms, skipped, rejected).
    - skipped: no deterministic enricher exists for their discovery_source yet.
    - rejected: failed entity-type filter (fund vehicle/institutional entity), OR passed it
      but websearch entity resolution found no operating site distinct from the filing
      vehicle (per the explicit instruction: unresolved -> reject, don't ship under the
      vehicle's name) — either way, a real outcome to log, not silently dropped.
    resolve_websites=False skips the guess-and-verify website pass (useful for fast
    iteration/tests that don't want live network calls per firm).
    use_websearch_fallback=False skips discovery/websearch.py's entity resolution for firms
    the domain guess couldn't place a website for (also for fast iteration)."""
    candidates = load_candidates()
    firms: list[Firm] = []
    skipped: list[DiscoveryRecord] = []
    rejected: list[RejectedCandidate] = []

    for record in candidates:
        entity_check = check_entity_type(record.name_as_found)
        if entity_check.rejected:
            rejected.append(RejectedCandidate(
                name=record.name_as_found, discovery_source=record.discovery_source,
                discovery_url=record.discovery_url, reason=entity_check.reason,
                evidence_span=entity_check.evidence_span,
            ))
            continue

        firm = enrich_candidate(record)
        if firm is None:
            skipped.append(record)
            continue

        if record.discovery_source in ("SEC EDGAR Form D", "SEC EDGAR 13F Filer List"):
            cik = extract_cik(record.notes)
            if cik:
                firm = enrich_from_submissions(firm, cik)

        if resolve_websites:
            firm = enrich_website_for_firm(firm)

        if use_websearch_fallback and not firm.website:
            firm, resolved = enrich_candidate_via_search(firm)
            # Reject-if-unresolved only applies to EDGAR: that's specifically where a name can
            # be a filing vehicle distinct from the operating firm. ProPublica-sourced
            # foundations that simply have no crawlable website are a genuine, expected
            # opacity outcome (see DECISIONS.md on the SFO-opacity ceiling) — not shipping
            # them under a "vehicle name" that doesn't apply here, so they stay in the pool
            # and fall out naturally at classification (no description text -> UTD) instead.
            if not resolved and record.discovery_source == "SEC EDGAR Form D":
                rejected.append(RejectedCandidate(
                    name=firm.name, discovery_source=firm.discovery_source,
                    discovery_url=firm.discovery_url,
                    reason="Web search entity resolution found no operating site distinct "
                           "from the filing vehicle — rejected rather than shipped under the "
                           "vehicle's name.",
                    evidence_span=None,
                ))
                continue

        # Only run this fallback if enrichment didn't already classify from raw page text
        # (website_resolve.py / websearch.py's phrase classifier, 2026-07-26) — that pass sees
        # much more real text than description/thesis/blind_spots alone and must not be
        # overwritten by a weaker, later check that already failed to find anything.
        if firm.classification == Classification.UNKNOWN:
            result = classify(_classification_source_text(firm), firm_name=firm.name)
            firm.classification = result.classification
            firm.classification_evidence = result.evidence
            if result.evidence_span:
                firm.blind_spots = (firm.blind_spots or "") + f" Classification evidence span: {result.evidence_span!r}"

        firms.append(firm)

    return firms, skipped, rejected


def qualifying(firms: list[Firm]) -> list[Firm]:
    """A firm qualifies if there's affirmative evidence it IS a family office — that's a
    separate question from SFO-vs-MFO subtype (2026-07-26 evidence-class fix). SFO/MFO
    classification qualifies on its own (subtype determined = family office confirmed).
    evidence_class (A/B/C/D) qualifies independently of subtype — a firm can be confirmed as a
    family office via Wikidata/press/regulatory evidence while its subtype stays genuinely
    Unable to Determine, and that still counts; SFO/MFO subtype is not guessed to force a firm
    into one bucket or the other. A firm with neither a determined subtype NOR any evidence_class
    is a real Unable to Determine and does not count — that outcome is legitimate, not a failure."""
    return [f for f in firms if f.classification != Classification.UNKNOWN or f.evidence_class]


if __name__ == "__main__":
    firms, skipped, rejected = run_enrichment()
    qual = qualifying(firms)
    print(f"{len(firms)} firm(s) enriched, {len(qual)} qualifying (classified SFO/MFO), "
          f"{len(firms) - len(qual)} Unable to Determine (not counted).")
    print(f"{len(rejected)} candidate(s) rejected by entity-type filter (fund vehicle / "
          f"institutional entity, never reached enrichment).")
    print(f"{len(skipped)} candidate(s) skipped (no deterministic/LLM enricher for their source).")
    for f in qual[:1]:
        print("\nFirst qualifying Firm:")
        print(f.model_dump_json(indent=2))
