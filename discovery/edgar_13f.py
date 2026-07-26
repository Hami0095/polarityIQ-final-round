"""EDGAR 13F filer list — bulk, keyless, no rate limit. Uses EDGAR's quarterly full-index
(form.idx), which lists every filing of every form type for a quarter, filtered to 13F-HR
(institutional investment manager holdings reports). Structurally distinct from Form D
(discovery/edgar.py): a 13F filer is an operating investment manager that has to file because
it manages >$100M in 13(f) securities, not a fund vehicle being offered — this is exactly the
vehicle-vs-operator distinction the 74% Form D finding (2026-07-25, DECISIONS.md) identified,
approached from the other side. Most 13F filers are unrelated institutions (banks, mutual
funds, pension managers); name-filtering to "family" here is a coarse discovery pass, same as
the other connectors — entity_filter.py and classification.py do the real filtering downstream.

Only surfaces name + CIK + filing index URL here; there is no per-candidate address/phone on
the 13F cover page cheap enough to parse deterministically at bulk-index time, so enrichment
falls through to the same website domain-guess pass every other candidate goes through.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import requests

from dataset.schema import DiscoveryRecord
from discovery.store import add_candidates

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
FORM_IDX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/form.idx"

# form.idx is fixed-width text. The dashed rule line under the header is a single unbroken
# run of dashes (confirmed 2026-07-26 — no per-column gaps), so it's useless for finding
# column boundaries. Instead, locate each known column label's start position directly in the
# header line itself — the labels and their order are fixed across quarters.
HEADER_MARKER = "Form Type   Company Name"
COLUMN_LABELS = ["Form Type", "Company Name", "CIK", "Date Filed", "File Name"]


def _parse_form_idx(text: str) -> list[dict]:
    lines = text.splitlines()
    try:
        header_idx = next(i for i, l in enumerate(lines) if l.startswith(HEADER_MARKER))
    except StopIteration:
        return []
    header_line = lines[header_idx]

    col_starts = [header_line.index(label) for label in COLUMN_LABELS]
    col_names = COLUMN_LABELS

    rows = []
    for line in lines[header_idx + 2:]:
        if not line.strip():
            continue
        values = [line[a:b].strip() for a, b in zip(col_starts, col_starts[1:] + [None])]
        rows.append(dict(zip(col_names, values)))
    return rows


def discover_13f_family_offices(year: int, quarter: int, name_filter: str = "family") -> list[DiscoveryRecord]:
    url = FORM_IDX_URL.format(year=year, quarter=quarter)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    rows = _parse_form_idx(resp.text)
    records = []
    seen = set()
    for row in rows:
        if not row.get("Form Type", "").startswith("13F-HR"):
            continue
        name = row.get("Company Name", "").strip()
        if not name or name_filter not in name.lower() or name.lower() in seen:
            continue
        seen.add(name.lower())
        cik = row.get("CIK", "").strip()
        filename = row.get("File Name", "").strip()
        records.append(DiscoveryRecord(
            candidate_id=f"13f-{cik}",
            name_as_found=name,
            discovery_source="SEC EDGAR 13F Filer List",
            discovery_url=f"https://www.sec.gov/{filename}" if filename else None,
            discovery_query=f"13F-HR filers, {year} QTR{quarter}, name contains '{name_filter}'",
            discovered_at=datetime.now(timezone.utc).isoformat(),
            notes=f"CIK {cik}",
        ))
    return records


if __name__ == "__main__":
    results = discover_13f_family_offices(year=2026, quarter=2)
    print(f"Found {len(results)} unique 13F-HR filers with 'family' in the name")
    for r in results[:15]:
        print("-", r.name_as_found)
    add_candidates(results, raw_payload={"connector": "edgar_13f", "count": len(results)})
