"""Assemble the delivered dataset from enriched Firm records: run validation
checks, null out anything that fails, write CSV + rejected/audit log +
methodology summary generated from the actual data (not hand-written).
"""
from __future__ import annotations

import csv
from pathlib import Path

from urllib.parse import urlparse

from dataset.schema import Classification, Confidence, Firm, SourcedField
from validation.checks import MXCheckInconclusive, check_email, check_evidence_span, check_phone

FINAL_DIR = Path(__file__).resolve().parent.parent / "data" / "final"

SOURCE_CAP = 0.35  # hard budget, not a preference — see DECISIONS.md 2026-07-25 work item 1


class SourceConcentrationError(Exception):
    """Raised when a single discovery_source exceeds SOURCE_CAP of the qualifying
    set. This must halt assembly, not just print a warning — a dataset with a
    dominant source fails the brief's single most common failure mode."""


def source_mix(firms: list[Firm]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for firm in firms:
        counts[firm.discovery_source] = counts.get(firm.discovery_source, 0) + 1
    return counts


def _registrable_domain(url: str | None) -> str:
    if not url:
        return "(no discovery_url)"
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    # collapse EDGAR/ProPublica per-CIK/per-org subpaths to their host — the
    # concentration risk is "one convenient website", not literal domain string
    return netloc or "(unparseable)"


def domain_mix(firms: list[Firm]) -> dict[str, int]:
    """Missing discovery_url is excluded from the mix entirely — that's a
    data-completeness gap, not evidence of domain concentration, and folding
    it in would make every record without a URL count against every other
    domain's ceiling."""
    counts: dict[str, int] = {}
    for firm in firms:
        if not firm.discovery_url:
            continue
        d = _registrable_domain(firm.discovery_url)
        counts[d] = counts.get(d, 0) + 1
    return counts


def _cap_violations(counts: dict[str, int], total: int, cap: float) -> dict[str, int]:
    return {k: c for k, c in counts.items() if c / total > cap}


def enforce_source_cap(firms: list[Firm], cap: float = SOURCE_CAP) -> None:
    """Two independent checks, same cap, same hard-fail: channel-level
    (self-assigned discovery_source label) and domain-level (registrable
    domain of discovery_url). Channel-level alone lets whoever names the
    channels decide whether the cap bites — three billionaire-list records
    from two listicle domains once passed as "Regional/Sector Directory".
    If channel-level passes but domain-level fails, domain-level wins."""
    total = len(firms)

    channel_counts = source_mix(firms)
    channel_violations = _cap_violations(channel_counts, total, cap)

    domain_counts = domain_mix(firms)
    domain_total = sum(domain_counts.values()) or 1
    domain_violations = _cap_violations(domain_counts, domain_total, cap)

    if channel_violations or domain_violations:
        lines = []
        for src, c in channel_violations.items():
            lines.append(f"  [channel] {src}: {c}/{total} = {100*c/total:.0f}% (cap is {100*cap:.0f}%)")
        for dom, c in domain_violations.items():
            lines.append(f"  [domain]  {dom}: {c}/{domain_total} = {100*c/domain_total:.0f}% (cap is {100*cap:.0f}%)")
        raise SourceConcentrationError(
            "Refusing to assemble dataset: one or more discovery sources/domains exceed the "
            f"{100*cap:.0f}% cap.\n" + "\n".join(lines) + "\n"
            "Add qualifying candidates from other discovery channels before re-running."
        )

FIELDS = [
    "firm_id", "name", "family_office_confirmed", "classification", "classification_evidence",
    "evidence_class", "evidence_class_detail",
    "description", "description_source", "description_confidence", "description_evidence_span",
    "investment_thesis", "investment_thesis_source", "investment_thesis_confidence",
    "sectors", "sectors_source",
    "aum", "aum_source", "aum_confidence",
    "hq_city", "hq_state", "hq_country", "domain", "website",
    "firm_email", "firm_email_checked_at", "firm_email_evidence_span",
    "firm_phone", "firm_phone_checked_at", "firm_phone_evidence_span",
    "discovery_source", "discovery_url", "discovery_method",
    "contact_actionability",
    "principal_1_name", "principal_1_title", "principal_1_email", "principal_1_phone", "principal_1_linkedin",
    "principal_2_name", "principal_2_title", "principal_2_email", "principal_2_phone", "principal_2_linkedin",
    "signal_1", "signal_1_source", "signal_2", "signal_2_source",
    "signal_3", "signal_3_source", "signal_4", "signal_4_source", "signal_5", "signal_5_source",
    "blind_spots",
]


def _check_email_field(firm_id: str, field_name: str, value: str, audit_log: list[dict],
                        inconclusive_log: list[dict]) -> tuple[str | None, bool]:
    """Returns (value_to_keep, was_nulled). On a genuine failure, nulls and
    logs to audit_log. On a network/DNS timeout (inconclusive), keeps the
    value as-is and logs to inconclusive_log instead — a timeout is not
    evidence the address is bad, and must not silently null real data."""
    try:
        ok, detail = check_email(value)
    except MXCheckInconclusive as e:
        inconclusive_log.append({"firm_id": firm_id, "field": field_name,
                                  "value": value, "reason": str(e)})
        return value, False
    if not ok:
        audit_log.append({"firm_id": firm_id, "field": field_name,
                           "attempted_value": value, "reason": detail})
        return None, True
    return value, False


def _sourced_fields(firm: Firm) -> list[tuple[str, SourcedField]]:
    fields = [
        ("description", firm.description), ("investment_thesis", firm.investment_thesis),
        ("sectors", firm.sectors), ("aum", firm.aum),
        ("firm_email", firm.firm_email), ("firm_phone", firm.firm_phone),
    ]
    for p in firm.principals:
        fields.append((f"principal:{p.full_name}:work_email", p.work_email))
        fields.append((f"principal:{p.full_name}:direct_phone", p.direct_phone))
        fields.append((f"principal:{p.full_name}:linkedin_url", p.linkedin_url))
    return fields


def enforce_evidence_spans(firm: Firm, audit_log: list[dict]) -> Firm:
    """Anti-fabrication gate, run before any other validation: every
    SourcedField's value must be a literal substring of its own
    evidence_span or it gets nulled and logged. See SourcedField docstring
    and the Real Capital Solutions incident in DECISIONS.md."""
    for field_name, field in _sourced_fields(firm):
        ok, detail = check_evidence_span(field)
        if not ok:
            audit_log.append({"firm_id": firm.firm_id, "field": field_name,
                               "attempted_value": field.value, "reason": f"evidence check: {detail}"})
            field.value = None
            field.confidence = Confidence.NONE
    return firm


def validate_and_null(firm: Firm, audit_log: list[dict], inconclusive_log: list[dict]) -> Firm:
    """Run real checks on email/phone; null the delivered field on a genuine
    failure and record it in the audit log. Inconclusive checks (DNS
    timeouts) leave the field untouched but get their own log so they're
    visible without being treated as proof of anything."""
    firm = enforce_evidence_spans(firm, audit_log)
    if firm.firm_email.value:
        kept, nulled = _check_email_field(firm.firm_id, "firm_email", firm.firm_email.value,
                                           audit_log, inconclusive_log)
        if nulled:
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
            _, nulled = _check_email_field(
                firm.firm_id, f"principal:{p.full_name}:work_email", p.work_email.value,
                audit_log, inconclusive_log,
            )
            if nulled:
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
    s3 = firm.signals[2] if len(firm.signals) > 2 else None
    s4 = firm.signals[3] if len(firm.signals) > 3 else None
    s5 = firm.signals[4] if len(firm.signals) > 4 else None
    return {
        "firm_id": firm.firm_id,
        "name": firm.name,
        "family_office_confirmed": "Yes" if firm.family_office_confirmed else "No",
        "classification": firm.classification_display(),
        "classification_evidence": firm.classification_evidence or "",
        "evidence_class": firm.evidence_class or "",
        "evidence_class_detail": firm.evidence_class_detail or "",
        "description": firm.description.value or "",
        "description_source": firm.description.source_url or "",
        "description_confidence": firm.description.confidence.value,
        "description_evidence_span": firm.description.evidence_span or "",
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
        "firm_email_checked_at": firm.firm_email.checked_at or "",
        "firm_email_evidence_span": firm.firm_email.evidence_span or "",
        "firm_phone": firm.firm_phone.value or "",
        "firm_phone_checked_at": firm.firm_phone.checked_at or "",
        "firm_phone_evidence_span": firm.firm_phone.evidence_span or "",
        "discovery_source": firm.discovery_source,
        "discovery_url": firm.discovery_url or "",
        "discovery_method": firm.discovery_method or "",
        "contact_actionability": firm.contact_actionability().value,
        "principal_1_name": p1.full_name if p1 else "",
        "principal_1_title": p1.title if p1 else "",
        "principal_1_email": p1.work_email.value if p1 else "",
        "principal_1_phone": p1.direct_phone.value if p1 else "",
        "principal_1_linkedin": p1.linkedin_url.value if p1 else "",
        "principal_2_name": p2.full_name if p2 else "",
        "principal_2_title": p2.title if p2 else "",
        "principal_2_email": p2.work_email.value if p2 else "",
        "principal_2_phone": p2.direct_phone.value if p2 else "",
        "principal_2_linkedin": p2.linkedin_url.value if p2 else "",
        "signal_1": s1.description if s1 else "",
        "signal_1_source": s1.source_url if s1 else "",
        "signal_2": s2.description if s2 else "",
        "signal_2_source": s2.source_url if s2 else "",
        "signal_3": s3.description if s3 else "",
        "signal_3_source": s3.source_url if s3 else "",
        "signal_4": s4.description if s4 else "",
        "signal_4_source": s4.source_url if s4 else "",
        "signal_5": s5.description if s5 else "",
        "signal_5_source": s5.source_url if s5 else "",
        "blind_spots": firm.blind_spots or "",
    }


def assemble(
    firms: list[Firm],
    rejected: list[Firm],
    batch_name: str = "pilot",
    enforce_cap: bool = True,
    cap: float = SOURCE_CAP,
) -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    audit_log: list[dict] = []
    inconclusive_log: list[dict] = []

    validated = [validate_and_null(f, audit_log, inconclusive_log) for f in firms]

    if inconclusive_log:
        print(f"\nWARNING: {len(inconclusive_log)} email check(s) were inconclusive "
              "(DNS timeout, not a real failure) and were left AS-IS rather than nulled:")
        for row in inconclusive_log:
            print(f"  {row['firm_id']} / {row['field']}: {row['value']}")
        print("Re-run validation later to get a definitive answer for these.")

    if enforce_cap:
        # 2026-07-26: explicit, user-authorized override to 50% for this batch, after two full
        # fix cycles (broadened classification lexicon, three new discovery channels, two
        # evidence classes beyond first-party website self-description) still left the
        # qualifying set at exactly two channels (ADV, Wikidata) each landing at 48%. This is
        # not a silent bypass — cap is a real parameter, defaults to the standard 35%, and the
        # override plus the reason is logged here and in DECISIONS.md.
        enforce_source_cap(validated, cap=cap)  # raises SourceConcentrationError and halts

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

    source_counts = source_mix(validated)
    total = len(validated)
    print(f"\n{batch_name}: {total} qualifying firms, {len(rejected)} rejected, "
          f"{len(audit_log)} fields failed validation and were nulled.")
    print("Discovery source distribution (channel label):")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count} ({100*count/total:.0f}%)")
    dom_counts = domain_mix(validated)
    dom_total = sum(dom_counts.values()) or 1
    print("Discovery source distribution (registrable domain):")
    for dom, count in sorted(dom_counts.items(), key=lambda x: -x[1]):
        print(f"  {dom}: {count} ({100*count/dom_total:.0f}%)")

    print_contact_coverage(validated)
    print(f"\nWrote {out_csv}, {rejected_csv}, {audit_csv}")


def print_contact_coverage(firms: list[Firm]) -> None:
    def rate(pred, pool):
        pool = list(pool)
        if not pool:
            return "n/a"
        hit = sum(1 for f in pool if pred(f))
        return f"{hit}/{len(pool)} ({100*hit/len(pool):.0f}%)"

    groups = {"All": firms, "SFO": [f for f in firms if f.classification.value == "Single-Family Office"],
              "MFO": [f for f in firms if f.classification.value == "Multi-Family Office"],
              "Subtype unconfirmed": [f for f in firms if f.classification == Classification.UNKNOWN]}

    print("\nContact coverage:")
    for label, pool in groups.items():
        if not pool:
            continue
        named = rate(lambda f: any(p.full_name for p in f.principals), pool)
        firm_contact = rate(lambda f: bool(f.firm_email.value or f.firm_phone.value), pool)
        principal_contact = rate(
            lambda f: any(p.work_email.value or p.direct_phone.value for p in f.principals), pool
        )
        print(f"  {label} (n={len(pool)}): named principal {named} | firm-level contact "
              f"{firm_contact} | direct principal contact {principal_contact}")


if __name__ == "__main__":
    # Pipeline output ships; hand research only measures (see DECISIONS.md, Question 0 and the
    # rebuild that followed it). This entrypoint runs the real discovery->enrichment pipeline
    # from whatever is in the candidate store — it no longer imports hand-authored records.
    from enrichment.pipeline import qualifying, run_enrichment

    firms, skipped, entity_rejected = run_enrichment()
    qual = qualifying(firms)
    print(f"{len(skipped)} candidate(s) skipped: no deterministic/LLM enricher available for "
          "their discovery_source, or the primary source was unreachable/unparseable.")
    print(f"{len(entity_rejected)} candidate(s) rejected by entity-type filter (fund vehicle / "
          "institutional entity).")
    print(f"{len(firms) - len(qual)} enriched firm(s) classified Unable to Determine — "
          "not counted toward the qualifying set.")
    assemble(qual, rejected=[], batch_name="pilot")
