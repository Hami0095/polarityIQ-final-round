"""Ground-truth fixture (NOT a shipped record source) — see hand_verified_ground_truth_1.py
for the full provenance note. Originally "batch 3", hand-researched 2026-07-25.

Excession (Musk), Willett Advisors (Bloomberg), and Cascade Investment (Gates) were removed
from this fixture on 2026-07-25: all three trace to two billionaire-listicle domains
(familyofficehub.io, altss.com), which is the single-source-dressed-as-diversification pattern
the concentration cap exists to catch; none carry a reachable contact or first-party site; and
Cascade's AUM cell put Gates's personal fortune in an AUM field, single-sourced to Wikipedia —
the same category error as treating 13F holdings as AUM, which this project correctly declined
to do elsewhere (Virtus). See DECISIONS.md 2026-07-25 for the full reasoning.
"""
from __future__ import annotations

from dataset.schema import Classification, Confidence, Firm, Principal, Signal, SourcedField

SF = SourcedField

BATCH3_FIRMS: list[Firm] = [
    Firm(
        firm_id="angeles-family-office",
        name="Angeles Family Office",
        description=SF(
            value=(
                "Family office division of Angeles Wealth Management (Santa Monica, CA), "
                "launched via the acquisition of XO Capital; serves generationally wealthy "
                "families in the $100M-$1B range."
            ),
            source_url="https://www.businesswire.com/news/home/20260113937854/en/Angeles-Wealth-Management-Acquires-XO-Capital-Launches-Angeles-Family-Office",
            verification_method="press release, corroborated by Los Angeles Business Journal coverage",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(
            value="Angeles Wealth Management + Angeles Investment Advisors: $2.5B+ private "
            "wealth, $40B+ institutional advised assets, ~100 client relationships (firm-wide, "
            "not specific to the family-office division)",
            source_url="https://labusinessjournal.com/finance/angeles-wealth-dips-into-family-office-work/",
            verification_method="press, corroborated by businesswire.com release",
            confidence=Confidence.MEDIUM,
        ),
        hq_city="Santa Monica",
        hq_state="CA",
        hq_country="United States of America",
        domain="angelesinvestments.com",
        website="https://www.angelesinvestments.com/private-wealth",
        classification=Classification.MFO,
        classification_evidence="Explicitly serves ~100 affluent client families through a "
        "shared advisory platform, not one family's wealth — self-described 'Goldilocks' "
        "positioning between boutique SFO and large institutional MFO, but structurally an MFO.",
        classification_source_url="https://labusinessjournal.com/finance/angeles-wealth-dips-into-family-office-work/",
        discovery_source="Regional Business Press",
        discovery_url="https://labusinessjournal.com/finance/angeles-wealth-dips-into-family-office-work/",
        principals=[
            Principal(
                first_name="Jonathan", last_name="Foster", full_name="Jonathan R. Foster",
                title="President and CEO, Angeles Wealth Management",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="Adam", last_name="Stern", full_name="Adam Stern",
                title="CEO, Angeles Family Office (via XO Capital acquisition)",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
        ],
        signals=[
            Signal(
                signal_type="hire",
                description="Acquired XO Capital to launch Angeles Family Office; XO Capital "
                "founder Adam Stern became CEO of the new family office division, Jason "
                "Oclaray became its president.",
                source_url="https://www.businesswire.com/news/home/20260113937854/en/Angeles-Wealth-Management-Acquires-XO-Capital-Launches-Angeles-Family-Office",
                confidence=Confidence.HIGH,
            )
        ],
        blind_spots=(
            "AUM figure is for the whole Angeles Wealth/Angeles Investment Advisors platform, "
            "not isolated to the family-office division specifically — noted rather than "
            "presented as a clean division-level number. Did not fetch angelesinvestments.com "
            "directly for individual contact info in this pass."
        ),
    ),
]
