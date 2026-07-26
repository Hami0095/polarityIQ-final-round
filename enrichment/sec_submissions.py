"""SEC submissions API (data.sec.gov/submissions/CIK##########.json) — keyless, needs only a
real User-Agent. Gives business address, phone, and (sometimes) website directly from EDGAR's
own entity record for any CIK. Built 2026-07-26 specifically for 13F and Form D candidates,
which otherwise carry almost nothing (13F only has a name+CIK from the bulk filer list; Form D
only gets an issuer phone from primary_doc.xml) — this is real, structured ground truth for the
SFO-heavy candidates this project has been struggling to enrich at all.
"""
from __future__ import annotations

import re
from datetime import date

from dataset.schema import Confidence, Firm, SourcedField
from enrichment.fetch import fetch

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"


def enrich_from_submissions(firm: Firm, cik: str) -> Firm:
    """Fills hq_city/hq_state/hq_country/firm_phone/website from the SEC submissions API,
    ONLY where the firm doesn't already have a value — same never-overwrite-a-deterministic-
    field policy as every other enricher in this pipeline."""
    try:
        result = fetch(SUBMISSIONS_URL.format(cik=cik))
        import json
        data = json.loads(result.raw)
    except Exception:
        return firm

    business = (data.get("addresses") or {}).get("business") or {}
    phone = data.get("phone") or ""
    website = data.get("website") or ""

    if not firm.hq_city and business.get("city"):
        firm.hq_city = business["city"]
    if not firm.hq_state and business.get("stateOrCountry"):
        firm.hq_state = business["stateOrCountry"]
    if not firm.hq_country and business.get("isForeignLocation"):
        firm.hq_country = business.get("stateOrCountryDescription")

    if not firm.firm_phone.value and phone:
        firm.firm_phone = SourcedField(
            value=phone, source_url=SUBMISSIONS_URL.format(cik=cik),
            verification_method="SEC submissions API (data.sec.gov), 'phone' field",
            confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
            evidence_span=f'"phone": "{phone}"', fetched_at=result.fetched_at,
            source_doc_len=len(result.raw),
        )

    if not firm.website and website and website.lower() not in ("none", "n/a"):
        firm.website = website if website.startswith("http") else f"https://{website}"
        firm.domain = firm.website.split("//", 1)[-1].split("/", 1)[0]

    return firm


def extract_cik(notes: str | None) -> str | None:
    if not notes:
        return None
    m = re.search(r"CIK\s*(\d+)", notes)
    return m.group(1) if m else None
