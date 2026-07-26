"""Entity-type rejection: runs BEFORE classification. A record that looks like a pooled fund
vehicle, an institutional asset manager, or a bank/trust/law/accounting firm serving the family
office segment never reaches SFO/MFO classification — it's rejected here, with the literal
phrase that triggered rejection kept as evidence, and logged to the rejected file with a reason.

Built after the EDGAR discovery-viability check (2026-07-25, DECISIONS.md): 74% of the 43 EDGAR
Form D full-text matches for "family office" were pooled fund vehicles (Wilshire, Lazard,
Geller's own fund products, Point72/Cubist) rather than operating firms — carrying "family
office" words in a name or filing is exactly the pattern the brief disqualifies, and it turned
out to be the majority shape of this channel's output, not an edge case.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Structural fund-vehicle markers. Checked FIRST and override everything else — a name
# containing "Family Office" AND "Fund II, L.P." (e.g. "Wilshire Private Markets Family Office
# Fund II, L.P.") is a fund vehicle, full stop; the "family office" words don't get it a pass.
FUND_VEHICLE_PATTERNS: list[tuple[str, str]] = [
    (r"\bfund\s+[ivxlc]+\b", "roman-numeral fund series (Fund II/III/IV-style)"),
    (r"\bfund\s+\d+\b", "numbered fund series (Fund 1/2-style)"),
    (r"\bstrategies\b", "'Strategies' — institutional fund-product naming"),
    (r"\bportfolio\b", "'Portfolio' — pooled-product naming"),
    (r"\bspv\b", "SPV (special purpose vehicle)"),
    (r"\b(a\s+)?series\s+of\b", "'a series of' — sub-fund/series LLC structure"),
    (r"\bgp\s*,?\s*l\.?p\.?\b", "GP L.P. — fund general-partner vehicle"),
    (r"\boffshore\b", "'Offshore' — fund-product naming"),
    (r"\bco-investors?\b", "'Co-Investor(s)' — deal-vehicle naming"),
    (r"\bventures?\s+[ivxlc0-9]+\b", "numbered venture fund (Ventures II-style)"),
    (r"\betf\s+fund\b", "ETF fund product naming"),
    (r"\bfund\b", "'Fund' — a bare 'Fund' in a legal entity name denotes a pooled investment "
                  "vehicle, not an operating company, even without a numbered series"),
]

# Institutional-service markers. Only checked when the name does NOT itself contain a
# family-office-flavored phrase — "Lexington Family Office & Trust, LLC" should not be rejected
# just because it contains "Trust"; an unaffiliated third-party "XYZ Trust Company" should be.
FAMILY_OFFICE_SELF_MARKERS = ["family office", "family partners", "family wealth"]

INSTITUTIONAL_SERVICE_PATTERNS: list[tuple[str, str]] = [
    (r"\bbank\b", "'Bank' — depository institution, not an operating family office"),
    (r"\btrust\s+company\b", "'Trust Company' — third-party fiduciary institution"),
    (r"\bllp\b", "LLP — professional-services entity structure (typically a law/accounting firm)"),
    (r"\bcpa(s)?\b", "CPA(s) — accounting firm"),
    (r"\bcertified\s+public\s+accountants?\b", "accounting firm"),
    (r"\blaw\s+firm\b", "law firm"),
    (r"\battorneys?\b", "law firm"),
    (r"\bplacement\s+agent\b", "placement agent — serves family offices as clients, is not one"),
]


@dataclass
class EntityFilterResult:
    rejected: bool
    reason: str | None = None
    evidence_span: str | None = None


def check_entity_type(name: str) -> EntityFilterResult:
    """Returns rejected=True with a reason + the literal matched phrase as
    evidence_span if the name structurally looks like a fund vehicle or an
    institutional entity serving the segment rather than an operating
    family office. rejected=False means it passed this filter — it still
    has to clear SFO/MFO/UTD classification separately."""
    lower = name.lower()

    for pattern, reason in FUND_VEHICLE_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            return EntityFilterResult(
                rejected=True,
                reason=f"Entity-type rejection: {reason}",
                evidence_span=name[m.start():m.end()],
            )

    has_self_marker = any(marker in lower for marker in FAMILY_OFFICE_SELF_MARKERS)
    if not has_self_marker:
        for pattern, reason in INSTITUTIONAL_SERVICE_PATTERNS:
            m = re.search(pattern, lower)
            if m:
                return EntityFilterResult(
                    rejected=True,
                    reason=f"Entity-type rejection: {reason}",
                    evidence_span=name[m.start():m.end()],
                )

    return EntityFilterResult(rejected=False)
