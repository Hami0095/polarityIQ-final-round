"""Deterministic enrichment for ProPublica Nonprofit Explorer candidates.

The org detail endpoint returns structured JSON (name, address, city, state,
NTEE code). No LLM needed — same rationale as edgar_enrich.py. evidence_span
here is the raw JSON fragment (a formatted key:value line), since JSON has
no natural "quote" the way HTML/prose does.
"""
from __future__ import annotations

import re
from datetime import date

from dataset.schema import Confidence, DiscoveryRecord, Firm, SourcedField
from enrichment.fetch import fetch

ORG_URL = "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"


def enrich_propublica_candidate(record: DiscoveryRecord) -> Firm | None:
    ein_match = re.search(r"propublica-(\d+)", record.candidate_id)
    if not ein_match:
        return None
    ein = ein_match.group(1)

    try:
        result = fetch(ORG_URL.format(ein=ein))
        import json
        data = json.loads(result.raw)
    except Exception:
        return None

    org = data.get("organization") or {}
    name = org.get("name") or record.name_as_found
    if not name:
        return None

    city = org.get("city")
    state = org.get("state")
    firm_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    evidence_span = f'"city": "{city}", "state": "{state}"' if (city or state) else None

    return Firm(
        firm_id=firm_id or record.candidate_id,
        name=name,
        hq_city=city,
        hq_state=state,
        classification_evidence=(
            f"Linked private foundation found via ProPublica 990 index, query "
            f"'{record.discovery_query}'. A foundation is a bridge lead to a family's "
            f"operating investment vehicle, not proof of one — classification requires a "
            f"second source confirming the operating entity."
        ),
        discovery_source=record.discovery_source,
        discovery_url=f"https://projects.propublica.org/nonprofits/organizations/{ein}",
        discovery_method=f"ProPublica Nonprofit Explorer search, query={record.discovery_query!r}, EIN={ein}",
        blind_spots=(
            "Enriched from ProPublica 990 org record only (deterministic parse, no LLM). This "
            "is a foundation, not necessarily the operating family office — description, "
            "thesis, sectors, AUM, contacts, and confirmation of the operating entity all "
            "require a second enrichment pass before this record can qualify for delivery."
        ),
    )
