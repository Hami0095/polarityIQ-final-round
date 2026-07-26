"""Minimal enrichment for EDGAR 13F candidates: there is no cheap deterministic per-candidate
address/phone at bulk-index time (unlike Form D's primary_doc.xml or ADV's bulk CSV row), so
this just builds a bare Firm from the discovery record and lets it flow into the same website
domain-guess + classification steps every other candidate goes through.
"""
from __future__ import annotations

import re

from dataset.schema import DiscoveryRecord, Firm


def enrich_13f_candidate(record: DiscoveryRecord) -> Firm | None:
    name = record.name_as_found.strip()
    if not name:
        return None
    firm_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return Firm(
        firm_id=firm_id or record.candidate_id,
        name=name,
        classification_evidence=(
            "Filed a Form 13F-HR (institutional investment manager holdings report), meaning "
            "it manages >$100M in 13(f) securities and is a real operating investment manager, "
            "not a fund vehicle being offered. This alone is not affirmative SFO/MFO evidence — "
            "13F filers include banks, mutual fund complexes, and pension managers as well as "
            "family offices — requires a second source before classification can move off "
            "Unable to Determine."
        ),
        discovery_source=record.discovery_source,
        discovery_url=record.discovery_url,
        discovery_method=record.discovery_query,
        blind_spots=(
            "Enriched from the 13F filer list only (name + CIK, no address/phone available at "
            "bulk-index time). Description/thesis/sectors/AUM/contact and classification all "
            "require a second enrichment pass before this record can qualify for delivery."
        ),
    )
