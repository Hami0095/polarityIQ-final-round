"""Assemble the delivered dataset from enriched Firm records: run validation
checks, null out anything that fails, write CSV + rejected/audit log +
methodology summary generated from the actual data (not hand-written).
"""
from __future__ import annotations

import csv
from pathlib import Path

from dataset.schema import Confidence, Firm
from validation.checks import check_email, check_phone

FINAL_DIR = Path(__file__).resolve().parent.parent / "data" / "final"

FIELDS = [
    "firm_id", "name", "classification", "classification_evidence",
    "description", "description_source", "description_confidence",
    "investment_thesis", "investment_thesis_source", "investment_thesis_confidence",
    "sectors", "sectors_source",
    "aum", "aum_source", "aum_confidence",
    "hq_city", "hq_state", "hq_country", "domain", "website",
    "firm_email", "firm_email_validation",
    "firm_phone", "firm_phone_validation",
    "discovery_source", "discovery_url",
    "principal_1_name", "principal_1_title",
    "principal_2_name", "principal_2_title",
    "signal_1", "signal_1_source", "signal_2", "signal_2_source",
    "blind_spots",
]


def validate_and_null(firm: Firm, audit_log: list[dict]) -> Firm:
    """Run real checks on email/phone; null the delivered field on failure
    and record the failure in the audit log rather than silently dropping it."""
    if firm.firm_email.value:
        ok, detail = check_email(firm.firm_email.value)
        if not ok:
            audit_log.append({
                "firm_id": firm.firm_id, "field": "firm_email",
                "attempted_value": firm.firm_email.value, "reason": detail,
            })
            firm.firm_email.value = None
            firm.firm_email.confidence = Confidence.NONE

    if firm.firm_phone.value:
        ok, detail = check_phone(firm.firm_phone.value)
        if not ok:
            audit_log.append({
                "firm_id": firm.firm_id, "field": "firm_phone",
                "attempted_value": firm.firm_phone.value, "reason": detail,
            })
            firm.firm_phone.value = None
            firm.firm_phone.confidence = Confidence.NONE

    for p in firm.principals:
        if p.work_email.value:
            ok, detail = check_email(p.work_email.value)
            if not ok:
                audit_log.append({
                    "firm_id": firm.firm_id, "field": f"principal:{p.full_name}:work_email",
                    "attempted_value": p.work_email.value, "reason": detail,
                })
                p.work_email.value = None
                p.work_email.confidence = Confidence.NONE
        if p.direct_phone.value:
            ok, detail = check_phone(p.direct_phone.value)
            if not ok:
                audit_log.append({
                    "firm_id": firm.firm_id, "field": f"principal:{p.full_name}:direct_phone",
                    "attempted_value": p.direct_phone.value, "reason": detail,
                })
                p.direct_phone.value = None
                p.direct_phone.confidence = Confidence.NONE

    return firm


def to_row(firm: Firm) -> dict:
    p1 = firm.principals[0] if len(firm.principals) > 0 else None
    p2 = firm.principals[1] if len(firm.principals) > 1 else None
    s1 = firm.signals[0] if len(firm.signals) > 0 else None
    s2 = firm.signals[1] if len(firm.signals) > 1 else None
    return {
        "firm_id": firm.firm_id,
        "name": firm.name,
        "classification": firm.classification.value,
        "classification_evidence": firm.classification_evidence or "",
        "description": firm.description.value or "",
        "description_source": firm.description.source_url or "",
        "description_confidence": firm.description.confidence.value,
        "investment_thesis": firm.investment_thesis.value or "",
        "investment_thesis_source": firm.investment_thesis.source_url or "",
        "investment_thesis_confidence": firm.investment_thesis.confidence.value,
        "sectors": firm.sectors.value or "",
        "sectors_source": firm.sectors.source_url or "",
        "aum": firm.aum.value or "",
        "aum_source": firm.aum.source_url or "",
        "aum_confidence": firm.aum.confidence.value,
        "hq_city": firm.hq_city or "",
        "hq_state": firm.hq_state or "",
        "hq_country": firm.hq_country or "",
        "domain": firm.domain or "",
        "website": firm.website or "",
        "firm_email": firm.firm_email.value or "",
        "firm_email_validation": firm.firm_email.verification_method or "",
        "firm_phone": firm.firm_phone.value or "",
        "firm_phone_validation": firm.firm_phone.verification_method or "",
        "discovery_source": firm.discovery_source,
        "discovery_url": firm.discovery_url or "",
        "principal_1_name": p1.full_name if p1 else "",
        "principal_1_title": p1.title if p1 else "",
        "principal_2_name": p2.full_name if p2 else "",
        "principal_2_title": p2.title if p2 else "",
        "signal_1": s1.description if s1 else "",
        "signal_1_source": s1.source_url if s1 else "",
        "signal_2": s2.description if s2 else "",
        "signal_2_source": s2.source_url if s2 else "",
        "blind_spots": firm.blind_spots or "",
    }


def assemble(firms: list[Firm], rejected: list[Firm], batch_name: str = "pilot") -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    audit_log: list[dict] = []

    validated = [validate_and_null(f, audit_log) for f in firms]

    out_csv = FINAL_DIR / f"{batch_name}_dataset.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for firm in validated:
            writer.writerow(to_row(firm))

    rejected_csv = FINAL_DIR / f"{batch_name}_rejected.csv"
    with rejected_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["firm_id", "name", "discovery_source", "rejected_reason"])
        writer.writeheader()
        for firm in rejected:
            writer.writerow({
                "firm_id": firm.firm_id, "name": firm.name,
                "discovery_source": firm.discovery_source,
                "rejected_reason": firm.rejected_reason,
            })

    audit_csv = FINAL_DIR / f"{batch_name}_contact_audit_log.csv"
    with audit_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["firm_id", "field", "attempted_value", "reason"])
        writer.writeheader()
        for row in audit_log:
            writer.writerow(row)

    # source-concentration check
    source_counts: dict[str, int] = {}
    for firm in validated:
        source_counts[firm.discovery_source] = source_counts.get(firm.discovery_source, 0) + 1
    total = len(validated)
    print(f"\n{batch_name}: {total} qualifying firms, {len(rejected)} rejected, "
          f"{len(audit_log)} contact fields failed validation and were nulled.")
    print("Discovery source distribution:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / total
        flag = "  <-- FLAG: exceeds ~30-40% of the batch" if pct > 40 else ""
        print(f"  {src}: {count} ({pct:.0f}%){flag}")
    print(f"\nWrote {out_csv}, {rejected_csv}, {audit_csv}")


if __name__ == "__main__":
    from dataset.pilot_records import PILOT_FIRMS, REJECTED_FIRMS
    assemble(PILOT_FIRMS, REJECTED_FIRMS, batch_name="pilot")
