"""SEC Form ADV bulk data connector — no key, no rate limit, one large CSV download.

Built as the primary replacement for search-based discovery after DuckDuckGo started
rate-limiting mid-run (2026-07-25): this is a structurally different, keyless, bulk surface —
registered investment advisers, not fund offerings (the EDGAR Form D problem) — with real
structured fields (address, phone, website, CRD#) rather than requiring entity resolution at
all. A firm's own website is often already given directly in the bulk data, which sidesteps the
domain-guessing/search-based entity resolution this project has been fighting with.

Methodology note worth stating plainly: true single-family offices are largely exempt from
Investment Advisers Act registration under the family-office exemption (Advisers Act Rule
202(a)(11)(G)-1), so their near-absence from this dataset is itself informative about why this
segment is hard to discover — not a gap in this pipeline. This channel should be expected to
skew MFO-heavy for exactly that reason.

Deliberately NOT used for AUM or client-type classification signals in this pass: the bulk CSV's
Item 5D/5F numeric columns (client-type breakdown, assets under management by category) exist,
but this project doesn't have the ADV Part 1A form instructions on hand to confirm their exact
semantics with confidence, and a wrong AUM figure shipped with false confidence is exactly the
category of error this project has been careful to avoid elsewhere (the Cascade Investment
AUM-category mistake in the original ground-truth fixture). Address/phone/website are used
because those are unambiguous. AUM/classification-from-client-mix is left as documented future
work, not guessed at.
"""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from dataset.schema import DiscoveryRecord
from discovery.store import add_candidates

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
LISTING_PAGE = ("https://www.sec.gov/data-research/sec-markets-data/"
                "information-about-registered-investment-advisers-exempt-reporting-advisers")
# Confirmed working 2026-07-26 — kept as a fallback if the listing-page scrape below fails
# (e.g. SEC reorganizes the page), since a stale-but-real bulk file beats no discovery at all.
FALLBACK_ZIP_URL = ("https://www.sec.gov/files/investment/data/other/"
                     "information-about-registered-investment-advisers-exempt-reporting-advisers/"
                     "ia07012026.zip")

ROWS_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "adv_family_office_rows.json"


def _find_latest_zip_url() -> str:
    try:
        resp = requests.get(LISTING_PAGE, headers={"User-Agent": USER_AGENT}, timeout=20)
        resp.raise_for_status()
        links = re.findall(r'href="([^"]+\.zip)"', resp.text)
        # restrict to the actual bulk-data path — the page has other unrelated .zip links
        # (confirmed 2026-07-26: a "data_distribution" sample link matched a looser filter and
        # silently produced zero real rows) — and take the first non "-exempt" full roster.
        data_links = [l for l in links if "/investment/data/" in l.lower()]
        full_rosters = [l for l in data_links if "-exempt" not in l.lower()]
        if full_rosters:
            url = full_rosters[0]
            return url if url.startswith("http") else f"https://www.sec.gov{url}"
    except requests.exceptions.RequestException:
        pass
    return FALLBACK_ZIP_URL


def _download_rows() -> list[dict]:
    url = _find_latest_zip_url()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
    resp.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    with z.open(z.namelist()[0]) as f:
        text = io.TextIOWrapper(f, encoding="latin-1")
        return list(csv.DictReader(text))


def discover_family_offices(name_filter: str = "family office") -> list[DiscoveryRecord]:
    """Filters the full ADV roster to firms whose Primary Business Name contains
    `name_filter`. Same keyword-surfacing approach as the EDGAR/ProPublica connectors —
    entity_filter.py and classification.py do the real filtering downstream, this just
    narrows a huge bulk file to plausible candidates."""
    rows = _download_rows()
    matches = [r for r in rows if name_filter in (r.get("Primary Business Name") or "").lower()]

    cache: dict[str, dict] = {}
    records: list[DiscoveryRecord] = []
    for row in matches:
        crd = row.get("Organization CRD#", "").strip()
        if not crd:
            continue
        cache[crd] = row
        records.append(DiscoveryRecord(
            candidate_id=f"adv-{crd}",
            name_as_found=row.get("Primary Business Name", "").strip(),
            discovery_source="SEC Form ADV Bulk Data",
            discovery_url=f"https://adviserinfo.sec.gov/firm/summary/{crd}",
            discovery_query=f'Primary Business Name contains "{name_filter}"',
            discovered_at=datetime.now(timezone.utc).isoformat(),
            notes=f"CRD {crd}",
        ))

    ROWS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROWS_CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    return records


if __name__ == "__main__":
    results = discover_family_offices()
    print(f"Found {len(results)} ADV-registered firms with 'family office' in the name")
    for r in results[:10]:
        print("-", r.name_as_found, "|", r.discovery_url)
    add_candidates(results, raw_payload={"connector": "adv_bulk", "count": len(results)})
