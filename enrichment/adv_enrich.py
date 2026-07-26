"""Deterministic enrichment for SEC Form ADV Bulk Data candidates. Address/phone/website come
straight from the CSV row cached by discovery/adv_bulk.py — no LLM, no domain-guessing, no
search-based entity resolution needed, since the bulk data already IS the firm's own filed
contact information. evidence_span is the literal CSV field value (there's no HTML/XML tag to
quote, so the raw cell value doubles as its own evidence).
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from dataset.schema import Confidence, DiscoveryRecord, Firm, Principal, Signal, SourcedField
from enrichment.adv_schedule_a import get_contact_employee, get_principals

ROWS_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "adv_family_office_rows.json"


def _load_row(crd: str) -> dict | None:
    if not ROWS_CACHE_PATH.exists():
        return None
    cache = json.loads(ROWS_CACHE_PATH.read_text(encoding="utf-8"))
    return cache.get(crd)


def enrich_adv_candidate(record: DiscoveryRecord) -> Firm | None:
    crd_match = re.search(r"adv-(\d+)", record.candidate_id)
    if not crd_match:
        return None
    row = _load_row(crd_match.group(1))
    if not row:
        return None

    name = (row.get("Primary Business Name") or "").strip()
    if not name:
        return None

    city = (row.get("Main Office City") or "").strip() or None
    state = (row.get("Main Office State") or "").strip() or None
    country = (row.get("Main Office Country") or "").strip() or None
    phone_raw = (row.get("Main Office Telephone Number") or "").strip()
    website_raw = (row.get("Website Address") or "").strip()

    firm_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    firm_phone = SourcedField(confidence=Confidence.NONE)
    if phone_raw:
        firm_phone = SourcedField(
            value=phone_raw, source_url=record.discovery_url,
            verification_method="SEC Form ADV bulk data, 'Main Office Telephone Number' field",
            confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
            evidence_span=phone_raw, fetched_at=record.discovered_at, source_doc_len=len(phone_raw),
        )

    website = None
    corporate_linkedin = None
    if website_raw and website_raw.lower() not in ("none", "n/a", ""):
        full_url = website_raw if website_raw.startswith("http") else f"https://{website_raw}"
        # Some ADV filers put a LinkedIn/Facebook URL in the "Website Address" field instead
        # of an actual site (confirmed 2026-07-26: Matter Family Office). Fetching that would
        # both violate this project's own no-LinkedIn-scraping rule and not work anyway
        # (login wall) — route social-platform URLs to corporate_linkedin as a reference,
        # leave website blank so the domain-guess fallback gets a real chance instead.
        if any(social in full_url.lower() for social in ("linkedin.com", "facebook.com", "twitter.com", "x.com")):
            if "linkedin.com" in full_url.lower():
                corporate_linkedin = full_url
        else:
            website = full_url

    principals: list[Principal] = []
    for p in get_principals(crd_match.group(1)):
        principals.append(Principal(full_name=p["full_name"], title=p["title"]))

    pdf_url = f"https://reports.adviserinfo.sec.gov/reports/ADV/{crd_match.group(1)}/PDF/{crd_match.group(1)}.pdf"

    firm_email = SourcedField(confidence=Confidence.NONE)
    contact = get_contact_employee(crd_match.group(1))
    if contact:
        # Item 1.J/1.K contact employee — a separate person from Schedule A's principals in
        # general (e.g. an outside compliance consultant), so matched into the existing
        # principals list by name rather than assumed to be principal_1, and only added as a
        # new principal if genuinely not already there.
        if contact["email"]:
            firm_email = SourcedField(
                value=contact["email"], source_url=pdf_url,
                verification_method="SEC Form ADV Item 1.J/1.K, 'Electronic mail (e-mail) address' field",
                confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
                evidence_span=contact["email"], fetched_at=record.discovered_at,
                source_doc_len=len(contact["email"]),
            )
        existing = next((p for p in principals if p.full_name and
                          p.full_name.strip().lower() == contact["name"].strip().lower()), None)
        target = existing
        if target is None:
            target = Principal(full_name=contact["name"], title=contact["title"])
            principals.append(target)
        if contact["phone"]:
            target.direct_phone = SourcedField(
                value=contact["phone"], source_url=pdf_url,
                verification_method="SEC Form ADV Item 1.J/1.K, 'Telephone number' field",
                confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
                evidence_span=contact["phone"], fetched_at=record.discovered_at,
                source_doc_len=len(contact["phone"]),
            )
        if contact["email"]:
            target.work_email = SourcedField(
                value=contact["email"], source_url=pdf_url,
                verification_method="SEC Form ADV Item 1.J/1.K, 'Electronic mail (e-mail) address' field",
                confidence=Confidence.HIGH, checked_at=date.today().isoformat(),
                evidence_span=contact["email"], fetched_at=record.discovered_at,
                source_doc_len=len(contact["email"]),
            )

    signals: list[Signal] = []
    filing_date = (row.get("Latest ADV Filing Date") or "").strip()
    if filing_date:
        signals.append(Signal(
            signal_type="news",
            description=f"Form ADV amendment filed {filing_date}",
            signal_date=filing_date,
            source_url=f"https://reports.adviserinfo.sec.gov/reports/ADV/{crd_match.group(1)}/PDF/{crd_match.group(1)}.pdf",
            confidence=Confidence.HIGH,
        ))

    return Firm(
        firm_id=firm_id or record.candidate_id,
        name=name,
        hq_city=city, hq_state=state, hq_country=country,
        website=website,
        corporate_linkedin=corporate_linkedin,
        domain=website.split("//", 1)[-1].split("/", 1)[0] if website else None,
        firm_phone=firm_phone,
        firm_email=firm_email,
        principals=principals,
        signals=signals,
        classification_evidence=(
            "Named as a registered investment adviser in SEC Form ADV bulk data with 'family "
            "office' in its filed business name. This alone is only naming evidence, not proof "
            "of SFO/MFO status per this project's own rule against inferring classification "
            "from a name — requires affirmative single/multi-family language from a second "
            "source before classification can move off Unable to Determine. Note: a firm "
            "appearing here at all is mild evidence AGAINST being a true single-family office, "
            "since SFOs are largely exempt from Advisers Act registration; this channel should "
            "skew MFO-heavy for that reason."
        ),
        discovery_source=record.discovery_source,
        discovery_url=record.discovery_url,
        discovery_method=f"SEC Form ADV bulk roster, CRD {crd_match.group(1)}",
        blind_spots=(
            "Enriched from Form ADV bulk CSV only (deterministic parse, no LLM). Address/phone/"
            "website taken directly from the filing. Principal name(s)/title(s), where present, "
            "come from that same filing's Schedule A (parsed from the firm's own ADV PDF report "
            "at reports.adviserinfo.sec.gov) — no email/phone was constructed for them, since "
            "Schedule A carries no contact info, only name/title/ownership. firm_email and any "
            "principal work_email/direct_phone come from Item 1.J (Chief Compliance Officer) or "
            "1.K (Additional Regulatory Contact Person) ONLY where the filer actually filled "
            "that optional field — checked all 14 pilot ADV firms directly and confirmed every "
            "one left 1.J/1.K blank (Schedule A already discloses the CCO's name via a required "
            "field, so most exempt reporting advisers skip re-entering it in this separate, "
            "optional section); this is a verified negative result, not a gap in the extraction. "
            "Item 5D/5F client-type and AUM columns "
            "exist in the source data but were NOT used to set aum or classification — this "
            "project does not have the ADV Part 1A form instructions on hand to confirm their "
            "exact column semantics with confidence, and an unverified AUM figure is worse than "
            "a blank one. Description/investment thesis/sectors/AUM and classification all "
            "require a second enrichment pass (firm website / press) before this record can "
            "qualify for delivery."
        ),
    )
