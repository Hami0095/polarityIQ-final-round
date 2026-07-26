"""Deterministic enrichment for Wikidata candidates. Headquarters city and website come
straight from the SPARQL result cached by discovery/wikidata.py — structured Wikidata claims,
not guessed. evidence_span is the Wikidata item URI itself (the claim is checkable by opening
that page), since there's no fetched document text to quote a substring from at this stage.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from dataset.schema import Confidence, DiscoveryRecord, Firm, SourcedField

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "wikidata_rows.json"


def _load_row(qid: str) -> dict | None:
    if not CACHE_PATH.exists():
        return None
    return json.loads(CACHE_PATH.read_text(encoding="utf-8")).get(qid)


def enrich_wikidata_candidate(record: DiscoveryRecord) -> Firm | None:
    qid_match = re.search(r"wikidata-(Q\d+)", record.candidate_id)
    if not qid_match:
        return None
    row = _load_row(qid_match.group(1))
    if not row:
        return None

    name = row.get("name", "").strip()
    if not name:
        return None

    firm_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    website = row.get("website") or None
    hq = row.get("hq") or None
    item_uri = row.get("item_uri")

    # Evidence Class A (2026-07-26): instance/subclass-of Q751314 ("family office") on Wikidata
    # is structured, third-party, curated classification evidence — affirmative evidence the
    # entity IS a family office, distinct from the separate question of SFO-vs-MFO subtype.
    # Previously this only produced classification_evidence text and left the firm sitting in
    # Unable to Determine for lack of a resolvable website — backwards, since the qualifying
    # evidence was already in hand. Does NOT guess SFO/MFO subtype from this alone; that stays
    # Unable to Determine unless a second source (website, press) supplies it, per the
    # never-infer-from-a-name-or-single-weak-signal rule.
    return Firm(
        firm_id=firm_id or record.candidate_id,
        name=name,
        hq_city=hq,
        website=website,
        domain=website.split("//", 1)[-1].split("/", 1)[0] if website else None,
        evidence_class="A",
        evidence_class_detail=(
            f"Wikidata instance/subclass-of claim: entity is classified under 'family office' "
            f"(Q751314). SPARQL claim: {item_uri} wdt:P31/wdt:P279* wd:Q751314."
        ),
        classification_evidence=(
            f"Confirmed as a family office via Wikidata structured classification (Evidence "
            f"Class A): {item_uri} is classified instance/subclass-of Q751314 'family office'. "
            f"This is affirmative evidence the entity IS a family office — a third-party, "
            f"curated classification, not a name-based guess. SFO-vs-MFO subtype is a "
            f"separate question this claim does not answer and is NOT inferred from it; "
            f"subtype stays Unable to Determine unless a second source (website, press) "
            f"supplies single/multi-family language."
        ),
        classification_source_url=item_uri,
        discovery_source="Wikidata",
        discovery_url=record.discovery_url,
        discovery_method=f"Wikidata SPARQL, item {qid_match.group(1)}",
        blind_spots=(
            "Enriched from a Wikidata item's structured claims only (deterministic, no LLM). "
            "Description/investment thesis/sectors/AUM/contact and SFO-vs-MFO subtype all "
            "require a second enrichment pass (firm website / press) — this record qualifies "
            "for the dataset (confirmed family office, Evidence Class A) but its subtype and "
            "most fields remain unverified beyond that."
        ),
    )
