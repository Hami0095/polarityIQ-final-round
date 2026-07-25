"""SEC EDGAR full-text search connector.

Uses the public EDGAR full-text search API (efts.sec.gov) to find Form D
filings (private placement notices) whose issuer name or filing text
mentions "family office". Form D is the most reachable EDGAR signal for
family offices since most are SEC-exempt reporting advisers and don't file
10-Ks/8-Ks themselves, but they often appear as issuers or investors in
Form D notices for the vehicles they run.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from dataset.schema import DiscoveryRecord
from discovery.store import add_candidates

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


def search_form_d(query: str = '"family office"', max_pages: int = 5) -> list[DiscoveryRecord]:
    headers = {"User-Agent": USER_AGENT}
    records: list[DiscoveryRecord] = []
    seen_names: set[str] = set()

    for page in range(max_pages):
        params = {"q": query, "forms": "D", "from": page * 10}
        resp = requests.get(SEARCH_URL, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break

        for h in hits:
            src = h["_source"]
            names = src.get("display_names", [])
            if not names:
                continue
            name = names[0].split(" (CIK")[0].strip()
            key = name.lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            cik = None
            if "(CIK" in names[0]:
                cik = names[0].split("(CIK")[-1].replace(")", "").strip()

            adsh = h["_id"].split(":")[0]
            filing_url = None
            if cik and adsh:
                acc_nodash = adsh.replace("-", "")
                filing_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
                )
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}"

            records.append(
                DiscoveryRecord(
                    candidate_id=f"edgar-formd-{cik or name}",
                    name_as_found=name,
                    discovery_source="SEC EDGAR Form D",
                    discovery_url=filing_url,
                    discovery_query=query,
                    discovered_at=datetime.now(timezone.utc).isoformat(),
                    notes=f"CIK {cik}" if cik else None,
                )
            )
        time.sleep(0.3)  # be polite to SEC's API

    return records


if __name__ == "__main__":
    results = search_form_d(max_pages=5)
    print(f"Found {len(results)} unique candidate names from Form D full-text search")
    for r in results[:10]:
        print("-", r.name_as_found, "|", r.discovery_url)
    add_candidates(results, raw_payload={"connector": "edgar_form_d", "count": len(results)})
