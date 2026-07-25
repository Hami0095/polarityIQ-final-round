"""ProPublica Nonprofit Explorer connector.

Many single-family offices run a linked private foundation (files a 990-PF)
even though the operating company itself isn't a public filer. Searching
ProPublica's public 990 index for family-office-flavored terms surfaces
those foundations, which is a usable discovery lead back to the family
and its office.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from dataset.schema import DiscoveryRecord
from discovery.store import add_candidates

SEARCH_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"

QUERIES = [
    "family office",
    "family foundation",
    "family wealth",
]


def search(queries: list[str] = QUERIES) -> list[DiscoveryRecord]:
    records: list[DiscoveryRecord] = []
    seen: set[str] = set()

    for q in queries:
        resp = requests.get(SEARCH_URL, params={"q": q}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for org in data.get("organizations", []):
            name = org.get("name", "").strip()
            ein = org.get("ein")
            key = (name.lower(), ein)
            if not name or key in seen:
                continue
            seen.add(key)

            records.append(
                DiscoveryRecord(
                    candidate_id=f"propublica-{ein}",
                    name_as_found=name,
                    discovery_source="ProPublica Nonprofit Explorer (990)",
                    discovery_url=f"https://projects.propublica.org/nonprofits/organizations/{ein}"
                    if ein
                    else None,
                    discovery_query=q,
                    discovered_at=datetime.now(timezone.utc).isoformat(),
                    notes=f"City: {org.get('city')}, State: {org.get('state')}",
                )
            )
        time.sleep(0.3)

    return records


if __name__ == "__main__":
    results = search()
    print(f"Found {len(results)} unique candidate orgs from ProPublica 990 search")
    for r in results[:10]:
        print("-", r.name_as_found, "|", r.notes)
    add_candidates(results, raw_payload={"connector": "propublica_990", "count": len(results)})
