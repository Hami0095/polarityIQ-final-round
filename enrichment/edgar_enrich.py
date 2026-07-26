"""Deterministic enrichment for SEC EDGAR Form D candidates.

Form D's primary_doc.xml is a fixed, machine-readable schema (issuer name,
address, phone). No LLM needed here — this is exactly the case Correction 1
says should stay deterministic. evidence_span is the raw XML fragment the
value was read from, so the same anti-fabrication validation gate applies
uniformly whether a field came from regex or from the LLM path.
"""
from __future__ import annotations

import re
from datetime import date

from dataset.schema import Confidence, DiscoveryRecord, Firm, SourcedField
from enrichment.fetch import fetch

_TAG = lambda name: re.compile(rf"<{name}>(.*?)</{name}>", re.IGNORECASE | re.DOTALL)

FIELD_TAGS = {
    "entityName": _TAG("entityName"),
    "street1": _TAG("street1"),
    "city": _TAG("city"),
    "stateOrCountry": _TAG("stateOrCountryDescription"),
    "phoneNumber": _TAG("issuerPhoneNumber"),
}


def _extract(raw: str, tag_re: re.Pattern) -> tuple[str | None, str | None]:
    m = tag_re.search(raw)
    if not m:
        return None, None
    value = m.group(1).strip()
    if not value:
        return None, None
    return value, m.group(0)


def enrich_edgar_candidate(record: DiscoveryRecord) -> Firm | None:
    """Fetches the Form D primary_doc.xml for a candidate and builds a Firm
    with whatever the filing itself supports. Returns None (not a fabricated
    partial record) if the primary doc can't be located/parsed — that's a
    real gap to log in discovery, not a firm to ship with guessed fields."""
    if not record.discovery_url:
        return None

    doc_url = record.discovery_url.rstrip("/") + "/primary_doc.xml"
    try:
        result = fetch(doc_url)
    except Exception:
        return None

    raw = result.raw
    name, name_span = _extract(raw, FIELD_TAGS["entityName"])
    city, city_span = _extract(raw, FIELD_TAGS["city"])
    state, state_span = _extract(raw, FIELD_TAGS["stateOrCountry"])
    phone, phone_span = _extract(raw, FIELD_TAGS["phoneNumber"])

    if not name:
        return None

    firm_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    firm_phone = SourcedField(confidence=Confidence.NONE)
    if phone:
        firm_phone = SourcedField(
            value=phone, source_url=doc_url,
            verification_method="SEC EDGAR Form D primary_doc.xml, issuerPhoneNumber field",
            confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
            evidence_span=phone_span, fetched_at=result.fetched_at, source_doc_len=len(raw),
        )

    return Firm(
        firm_id=firm_id or record.candidate_id,
        name=name,
        hq_city=city,
        hq_state=state,
        firm_phone=firm_phone,
        classification_evidence=(
            f"Named issuer on a Form D filing whose full-text index was matched by the query "
            f"'{record.discovery_query}'. Classification (SFO/MFO/UTD) not determinable from "
            f"Form D alone — requires a second, independent source before this can be set to "
            f"anything but Unable to Determine."
        ),
        discovery_source=record.discovery_source,
        discovery_url=record.discovery_url,
        discovery_method=f"EDGAR full-text search, query={record.discovery_query!r}, doc={doc_url}",
        blind_spots=(
            "Enriched from Form D primary_doc.xml only (deterministic parse, no LLM). "
            "Description, investment thesis, sectors, AUM, and classification not sourced from "
            "this filing and require a second enrichment pass (firm website / press) before "
            "this record can qualify for delivery."
        ),
    )
