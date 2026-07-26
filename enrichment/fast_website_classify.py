"""Fast classification-only website check for the 13F backlog (90-minute hard cap on this
pass — no time for enrichment/website_resolve.py's full multi-path LLM extraction sweep,
which fetches up to 7 subpaths per firm and runs an LLM call on each). This does exactly the
one thing route 2 of the classification gate needs: resolve the firm's own domain (reusing
website_resolve.resolve_website's guess-and-verify, itself just requests + a name/marker
check, no LLM), fetch ONLY the homepage, and run dataset.classification.classify() against
the raw page text directly — the same deterministic phrase classifier used everywhere else in
this project, just without the LLM description/thesis/aum extraction pass this task doesn't
need. No new classification mechanism, no lowered bar: same classify(), same SFO_MARKERS/
MFO_MARKERS, same "no affirmative language -> stays Unable to Determine" rule.
"""
from __future__ import annotations

from dataset.classification import classify
from dataset.schema import Classification, Firm
from enrichment.fetch import fetch
from enrichment.website_resolve import resolve_website


def classify_via_website(firm: Firm) -> Firm:
    if firm.classification != Classification.UNKNOWN:
        return firm
    url = firm.website or resolve_website(firm.name, timeout=5)
    if not url:
        firm.blind_spots = (firm.blind_spots or "") + (
            " Fast website-classification pass (13F backlog, 2026-07-26): no domain guess "
            "matched the firm name — no classification evidence available from this route."
        )
        return firm
    try:
        result = fetch(url)
    except Exception:
        firm.blind_spots = (firm.blind_spots or "") + (
            f" Fast website-classification pass: matched {url} but re-fetch failed."
        )
        return firm
    firm.website = firm.website or url
    firm.domain = firm.domain or url.split("//", 1)[-1].split("/", 1)[0]
    page_result = classify(result.text, firm_name=firm.name)
    if page_result.classification != Classification.UNKNOWN:
        firm.classification = page_result.classification
        firm.classification_evidence = page_result.evidence
        firm.classification_source_url = result.url
    else:
        firm.blind_spots = (firm.blind_spots or "") + (
            f" Fast website-classification pass: fetched {url}, no affirmative SFO/MFO "
            "phrase found — stays Unable to Determine (this pass did not run the fuller "
            "LLM description/thesis extraction other channels get, homepage-only, "
            "time-boxed)."
        )
    return firm
