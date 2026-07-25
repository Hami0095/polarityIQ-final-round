"""Batch 3: 4 more qualifying firms, added to push EDGAR's share of the
pilot below the enforced 35% cap. Sourced from billionaire-family-office
directory/list content (a distinct discovery channel from the ad hoc press
search used for Dara Holdings in the original pilot) and regional business
press, enriched 2026-07-25.
"""
from __future__ import annotations

from dataset.schema import Classification, Confidence, Firm, Principal, Signal, SourcedField

SF = SourcedField

BATCH3_FIRMS: list[Firm] = [
    Firm(
        firm_id="excession-musk-family-office",
        name="Excession LLC (Elon Musk Family Office)",
        description=SF(
            value=(
                "Single-family office of Elon Musk, set up in 2016 and run by managing "
                "director Jared Birchall (former Morgan Stanley SVP). A compact executive "
                "office (~10 staff) that mobilizes capital and counsel around Musk's operating "
                "companies rather than a traditional diversified allocator."
            ),
            source_url="https://familyofficehub.io/blog/the-elon-musk-family-office-excession/",
            verification_method="industry profile, corroborated by Bloomberg company profile and Altss",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Concentrated around Musk's own operating companies (Tesla, SpaceX, The "
            "Boring Company, Neuralink, xAI); does not run a traditional LP allocation "
            "program or broadly commit to external funds.",
            source_url="https://familyofficehub.io/blog/the-elon-musk-family-office-excession/",
            verification_method="industry profile",
            confidence=Confidence.MEDIUM,
        ),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(confidence=Confidence.NONE),
        hq_state="TX",
        hq_country="United States of America",
        domain=None,
        website=None,
        classification=Classification.SFO,
        classification_evidence="Consistently and specifically described across multiple "
        "independent industry sources as Elon Musk's personal single-family office; "
        "Texas-domiciled LLC.",
        classification_source_url="https://familyofficehub.io/blog/the-elon-musk-family-office-excession/",
        discovery_source="Regional/Sector Directory (billionaire family office lists)",
        discovery_url="https://familyofficehub.io/single-family-offices-of-us-billionaires-and-hnwis/",
        principals=[
            Principal(
                first_name="Jared", last_name="Birchall", full_name="Jared Birchall",
                title="Managing Director",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[],
        blind_spots=(
            "No first-party website found (consistent with Excession deliberately keeping a "
            "low public profile). Could not verify AUM as a specific number — sources cite "
            "Musk's total net worth (~$200B+, mostly illiquid equity in his own companies), "
            "which is not the same as assets under Excession's management, so left blank "
            "rather than conflating the two. No contact info found for Birchall or the firm."
        ),
    ),
    Firm(
        firm_id="willett-advisors-bloomberg",
        name="Willett Advisors (Michael Bloomberg Family Office)",
        description=SF(
            value=(
                "Family office managing the personal assets of Michael R. Bloomberg alongside "
                "the investment needs of Bloomberg Philanthropies; founded 2010, based in New "
                "York, led by CEO Steven Rattner (Quadrangle Group co-founder) since 2009."
            ),
            source_url="https://en.wikipedia.org/wiki/Willett_Advisors",
            verification_method="Wikipedia, corroborated by Altss and Capital Allocators podcast coverage",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Diversified across public markets, hedge funds, private equity and "
            "credit, real assets, and direct investments; mandate is to preserve/grow "
            "Bloomberg's wealth while funding Bloomberg Philanthropies.",
            source_url="https://en.wikipedia.org/wiki/Willett_Advisors",
            verification_method="Wikipedia",
            confidence=Confidence.MEDIUM,
        ),
        sectors=SF(
            value="Diversified: public markets, hedge funds, PE/credit, real assets, direct investments",
            source_url="https://en.wikipedia.org/wiki/Willett_Advisors",
            verification_method="Wikipedia",
            confidence=Confidence.MEDIUM,
        ),
        aum=SF(
            value="~$25B",
            source_url="https://en.wikipedia.org/wiki/Willett_Advisors",
            verification_method="single source (Wikipedia); not independently corroborated "
            "against a second domain in this pass",
            confidence=Confidence.MEDIUM,
        ),
        hq_city="New York",
        hq_state="NY",
        hq_country="United States of America",
        domain=None,
        website=None,
        classification=Classification.SFO,
        classification_evidence="Explicitly and consistently described as Michael Bloomberg's "
        "personal family office across multiple sources, serving one individual/family's "
        "wealth and an affiliated philanthropy, not outside clients.",
        classification_source_url="https://en.wikipedia.org/wiki/Willett_Advisors",
        discovery_source="Regional/Sector Directory (billionaire family office lists)",
        discovery_url="https://familyofficehub.io/single-family-offices-of-us-billionaires-and-hnwis/",
        principals=[
            Principal(
                first_name="Steven", last_name="Rattner", full_name="Steven Rattner",
                title="Chief Executive Officer",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[],
        blind_spots=(
            "No first-party website found/used. AUM figure sourced from a single domain "
            "(Wikipedia) — flagged Medium rather than High per the corroboration standard "
            "used elsewhere in this dataset. No contact info found for Rattner or the firm."
        ),
    ),
    Firm(
        firm_id="cascade-investment-gates",
        name="Cascade Investment, L.L.C. (Bill Gates Family Office)",
        description=SF(
            value=(
                "Single-family office and private holding company controlled by William H. "
                "Gates III, founded 1994, headquartered in Kirkland, WA, led by CIO Michael "
                "Larson. Manages Gates's personal investment assets separately from the Gates "
                "Foundation's endowment."
            ),
            source_url="https://en.wikipedia.org/wiki/Cascade_Investment",
            verification_method="Wikipedia, corroborated by SWFI institute profile and Altss",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Diversified across global public equities, venture capital, private "
            "equity, hedge fund strategies, and fund-manager investments; notable direct "
            "holdings include Canadian National Railway, Four Seasons Hotels, and Ecolab.",
            source_url="https://en.wikipedia.org/wiki/Cascade_Investment",
            verification_method="Wikipedia",
            confidence=Confidence.MEDIUM,
        ),
        sectors=SF(
            value="Diversified: public equities, venture capital, private equity, hedge funds",
            source_url="https://en.wikipedia.org/wiki/Cascade_Investment",
            verification_method="Wikipedia",
            confidence=Confidence.MEDIUM,
        ),
        aum=SF(
            value="$115B+ (Gates's personal fortune managed via Cascade; separate from the "
            "$67B Gates Foundation endowment)",
            source_url="https://en.wikipedia.org/wiki/Cascade_Investment",
            verification_method="single source (Wikipedia); not independently corroborated "
            "against a second domain in this pass",
            confidence=Confidence.MEDIUM,
        ),
        hq_city="Kirkland",
        hq_state="WA",
        hq_country="United States of America",
        domain=None,
        website=None,
        classification=Classification.SFO,
        classification_evidence="Explicitly and consistently described across independent "
        "sources as Bill Gates's personal single-family office/private holding company, "
        "distinct from the Gates Foundation.",
        classification_source_url="https://en.wikipedia.org/wiki/Cascade_Investment",
        discovery_source="Regional/Sector Directory (billionaire family office lists)",
        discovery_url="https://altss.com/profile/cascade-investment-llc-bill-gates-family-office",
        principals=[
            Principal(
                first_name="Michael", last_name="Larson", full_name="Michael Larson",
                title="Chief Investment Officer",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[],
        blind_spots=(
            "No first-party website found/used — Cascade deliberately keeps a low public "
            "profile. AUM figure single-sourced (Wikipedia), flagged Medium. No contact info "
            "found for Larson or the firm; this is expected for one of the most opaque SFOs "
            "in the market, not a pipeline gap."
        ),
    ),
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
