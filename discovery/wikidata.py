"""Wikidata SPARQL connector — free, keyless, no rate limit observed. Queries for items
classified (via instance-of/subclass-of transitive closure) under Q751314 ("family office"),
pulling headquarters location (P159) and official website (P856) where present — both are
already structured facts on the Wikidata item, not something to guess or search for.

Small yield (15 items as of 2026-07-26) but high per-record confidence: a Wikidata item with a
P856 website claim is citable straight to the Wikidata item page plus whatever reference the
claim itself carries.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from dataset.schema import DiscoveryRecord
from discovery.store import add_candidates

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "wikidata_rows.json"

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
SPARQL_URL = "https://query.wikidata.org/sparql"
FAMILY_OFFICE_QID = "Q751314"

QUERY = f"""
SELECT ?item ?itemLabel ?hqLabel ?website WHERE {{
  ?item wdt:P31/wdt:P279* wd:{FAMILY_OFFICE_QID} .
  OPTIONAL {{ ?item wdt:P159 ?hq . }}
  OPTIONAL {{ ?item wdt:P856 ?website . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""


def search() -> list[DiscoveryRecord]:
    try:
        resp = requests.get(SPARQL_URL, params={"query": QUERY, "format": "json"},
                             headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    data = resp.json()
    records = []
    cache: dict[str, dict] = {}
    seen = set()
    for b in data["results"]["bindings"]:
        name = b.get("itemLabel", {}).get("value", "").strip()
        item_uri = b.get("item", {}).get("value", "")
        qid = item_uri.rsplit("/", 1)[-1] if item_uri else None
        if not name or qid in seen:
            continue
        seen.add(qid)
        hq = b.get("hqLabel", {}).get("value")
        website = b.get("website", {}).get("value")
        cache[qid] = {"name": name, "item_uri": item_uri, "hq": hq, "website": website}
        records.append(DiscoveryRecord(
            candidate_id=f"wikidata-{qid}",
            name_as_found=name,
            discovery_source="Wikidata",
            discovery_url=item_uri or None,
            discovery_query=f"instance/subclass of wd:{FAMILY_OFFICE_QID}",
            discovered_at=datetime.now(timezone.utc).isoformat(),
            notes=f"hq={hq}; website={website}",
        ))

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    return records


if __name__ == "__main__":
    results = search()
    print(f"Found {len(results)} unique Wikidata items classified under 'family office'")
    for r in results:
        print("-", r.name_as_found, "|", r.notes)
    add_candidates(results, raw_payload={"connector": "wikidata", "count": len(results)})
