"""GROUND TRUTH FIXTURE — NOT A SHIPPED RECORD SOURCE.

Reclassified 2026-07-25 after a provenance review (see DECISIONS.md, "Question 0"). These 9
qualifying + 1 rejected firms were hand-enriched from live WebSearch/WebFetch research
conducted in-conversation on 2026-07-25 — i.e. field values were typed into this file by a
human-in-the-loop research pass, not emitted by code that fetched and parsed a source at
runtime. That is exactly the pattern the brief prohibits for delivered records: "must be
produced by the pipeline... not manually assembled record-by-record."

They are kept, not deleted, because they are still useful for a different purpose: a
hand-verified answer key. benchmark/ runs the real (rebuilt) pipeline and measures discovery
recall and field-level agreement against these values. The rule going forward is "pipeline
output ships, hand research only measures" — nothing in this file is written to
data/final/*.csv directly or backfilled into a pipeline-produced record.
"""
from __future__ import annotations

from dataset.schema import (
    Classification,
    Confidence,
    Firm,
    Principal,
    Signal,
    SourcedField,
)

SF = SourcedField  # alias for brevity


PILOT_FIRMS: list[Firm] = [
    Firm(
        firm_id="mactaggart-family-partners",
        name="Mactaggart Family & Partners",
        description=SF(
            value=(
                "Family office-backed real estate private equity co-investment platform of "
                "Western Heritable; principal commercial investment portfolios in London and "
                "New York, focused on adding value to real estate and holding core assets "
                "long-term."
            ),
            source_url="https://commercialobserver.com/company/mactaggart-family-partners/",
            verification_method="press profile, cross-checked against firm site",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value=(
                "Value-add commercial and residential real estate development, investment, and "
                "management, with emphasis on city-centre office and hotel developments and "
                "strategic land."
            ),
            source_url="https://mactaggartfp.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Real estate (commercial, residential, hospitality)",
            source_url="https://mactaggartfp.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        aum=SF(confidence=Confidence.NONE),
        hq_address="2 Babmaes Street",
        hq_city="London",
        hq_state=None,
        hq_country="United Kingdom",
        domain="mactaggartfp.com",
        website="https://mactaggartfp.com/",
        corporate_linkedin=None,
        firm_phone=SF(
            value="+44 20 7491 2948",
            source_url="https://mactaggartfp.com/",
            verification_method="listed directly on official site",
            confidence=Confidence.HIGH,
        ),
        classification=Classification.SFO,
        classification_evidence=(
            "Explicitly described in press as a 'family office-backed real estate private "
            "equity firm'; board led by multiple Mactaggart family members (Sir John, Philip, "
            "Jack, Sholto Mactaggart) as directors."
        ),
        classification_source_url="https://commercialobserver.com/company/mactaggart-family-partners/",
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001647951",
        principals=[
            Principal(
                first_name="Philip",
                last_name="Mactaggart",
                full_name="Philip Mactaggart",
                title="Chair",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="William",
                last_name="Laxton",
                full_name="William Laxton",
                title="CEO",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
        ],
        signals=[
            Signal(
                signal_type="investment",
                description="Acquired 134-136 Broadway, a 23,064 sq ft office building in "
                "Williamsburg, Brooklyn, for $18.8M with Caspi Development.",
                signal_date=None,
                source_url="https://rebusinessonline.com/caspi-development-mactaggart-family-acquire-office-building-in-williamsburg-for-18-8m/",
                confidence=Confidence.HIGH,
            ),
            Signal(
                signal_type="investment",
                description="Acquired three multifamily properties in Little Italy and Two "
                "Bridges (Manhattan) for $22.7M.",
                signal_date=None,
                source_url="https://commercialobserver.com/2018/12/mactaggart-family-partners-steven-rosenberg-abe-cohen-purchase-119-baxter-street-110-madison-street-33-henry-street/",
                confidence=Confidence.HIGH,
            ),
        ],
        blind_spots=(
            "Could not verify AUM (not disclosed); could not verify direct emails/phones for "
            "named principals; press signal dates approximate (article publish dates used as "
            "proxy, not confirmed deal-close dates)."
        ),
    ),
    Firm(
        firm_id="daddario-family-office",
        name="D'Addario Family Office LLC (DADA Holdings)",
        description=SF(
            value=(
                "Investment and management arm of the D'Addario Family Office, making control "
                "and passive investments across industries; also runs the Liv It Up Foundation "
                "supporting the neurodiverse community."
            ),
            source_url="https://dadaholdings.com/who-we-are",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(confidence=Confidence.NONE),
        hq_address="2400 E. Commercial Blvd., Suite 810",
        hq_city="Fort Lauderdale",
        hq_state="FL",
        hq_country="United States of America",
        domain="dadaholdings.com",
        website="https://dadaholdings.com/",
        corporate_linkedin=None,
        classification=Classification.SFO,
        classification_evidence=(
            "First-party site explicitly states the entity is 'the investment and management "
            "arm of the D'Addario Family Office'; linked private foundation is named for a "
            "specific family member (The David D'Addario Family Foundation), affirming single-"
            "family origin."
        ),
        classification_source_url="https://dadaholdings.com/who-we-are",
        discovery_source="ProPublica Nonprofit Explorer (990)",
        discovery_url="https://projects.propublica.org/nonprofits/organizations/61573658",
        principals=[
            Principal(
                first_name="David",
                last_name="D'Addario",
                full_name="David F. D'Addario",
                title="Principal / Family Member",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="Ryan",
                last_name="Boland",
                full_name="Ryan Boland",
                title="Chief Executive Officer",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
        ],
        signals=[],
        blind_spots=(
            "Could not verify investment thesis, sectors, or AUM — site describes the mandate "
            "generally but discloses no specifics. No recent signals found. Could not verify "
            "any principal contact info."
        ),
    ),
    Firm(
        firm_id="dara-holdings",
        name="Dara Holdings",
        description=SF(
            value=(
                "Family investment office of Lubna Olayan, a principal of Olayan Group, the "
                "Saudi family-owned conglomerate her father founded in 1947."
            ),
            source_url="https://www.bloomberg.com/news/articles/2025-02-21/billionaire-saudi-heiress-bets-on-female-founders-in-deal-spree",
            verification_method="press (Bloomberg), cross-checked against Wikipedia bio",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value=(
                "Backs female-founded/led startups in the UAE and wider Middle East, spanning "
                "AI, biotech, and fintech/health, alongside participation in larger growth "
                "rounds; supports a social-impact fund at the charity Alfanar."
            ),
            source_url="https://menafn.com/1109239501/Saudi-Billionaire-Lubna-Olayans-Dara-Holdings-Amplifies-Investments-In-Female-Led-UAE-Startups",
            verification_method="press, corroborated by Bloomberg coverage of the same pattern",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Venture/growth — AI, biotech/health, fintech",
            source_url="https://www.dakota.com/reports-blog/family-office-deal-tracker-june-2026",
            verification_method="press deal tracker",
            confidence=Confidence.MEDIUM,
        ),
        aum=SF(confidence=Confidence.NONE),
        hq_address=None,
        hq_city=None,
        hq_state=None,
        hq_country=None,
        domain=None,
        website=None,
        corporate_linkedin=None,
        classification=Classification.SFO,
        classification_evidence=(
            "Explicitly reported as the personal family office of a single named individual "
            "(Lubna Olayan), not a multi-client advisory business."
        ),
        classification_source_url="https://www.bloomberg.com/news/articles/2025-02-21/billionaire-saudi-heiress-bets-on-female-founders-in-deal-spree",
        discovery_source="Press search (WebSearch)",
        discovery_url="https://menafn.com/1109239501/Saudi-Billionaire-Lubna-Olayans-Dara-Holdings-Amplifies-Investments-In-Female-Led-UAE-Startups",
        principals=[
            Principal(
                first_name="Lubna",
                last_name="Olayan",
                full_name="Lubna Olayan",
                title="Principal",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[
            Signal(
                signal_type="investment",
                description="Participated in a $10M seed round for qeen, a Dubai-based AI "
                "startup co-founded by a former Google executive.",
                signal_date="2025-02",
                source_url="https://menafn.com/1109239501/Saudi-Billionaire-Lubna-Olayans-Dara-Holdings-Amplifies-Investments-In-Female-Led-UAE-Startups",
                confidence=Confidence.MEDIUM,
            ),
            Signal(
                signal_type="investment",
                description="Participated in a $550M round for Alan, a French health insurer.",
                signal_date="2026-06",
                source_url="https://www.dakota.com/reports-blog/family-office-deal-tracker-june-2026",
                confidence=Confidence.MEDIUM,
            ),
        ],
        blind_spots=(
            "Could not verify HQ address, domain/website, or AUM — no first-party site found "
            "in this pass. No official contact info found for the principal; all information "
            "sourced from press coverage rather than a primary filing or first-party site."
        ),
    ),
    Firm(
        firm_id="lexington-family-office-trust",
        name="Lexington Family Office & Trust, LLC",
        description=SF(
            value=(
                "Virtual family office serving high-net-worth and ultra-high-net-worth "
                "individuals, families, trusts, and charitable organizations with a goals-"
                "based, family-centric approach."
            ),
            source_url="https://www.bloomberg.com/profile/company/3858812Z:US",
            verification_method="press/company-profile aggregator",
            confidence=Confidence.MEDIUM,
        ),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(confidence=Confidence.NONE),
        hq_address=None,
        hq_city="Nashville",
        hq_state="TN",
        hq_country="United States of America",
        domain=None,
        website=None,
        corporate_linkedin=None,
        classification=Classification.MFO,
        classification_evidence=(
            "Firm description explicitly states it serves multiple unrelated HNW/UHNW clients "
            "('individuals, families, trusts, and charitable organizations') under a shared "
            "advisory platform — not one family's wealth."
        ),
        classification_source_url="https://www.bloomberg.com/profile/company/3858812Z:US",
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001551648",
        principals=[],
        signals=[],
        blind_spots=(
            "Could not verify founder/principal name, direct website, AUM, or thesis in this "
            "pass — would need a dedicated site visit or SEC IAPD lookup (JS-rendered, not "
            "fetchable with the current tool) to fill these in."
        ),
    ),
    Firm(
        firm_id="virtus-family-office",
        name="Virtus Family Office, LLC",
        description=SF(
            value="A multifamily office and independent wealth advisory firm providing "
            "personalized wealth management for high-net-worth families.",
            source_url="https://virtus-usa.com/en/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Wealth protection and growth, family governance, and legacy planning for "
            "select client families.",
            source_url="https://virtus-usa.com/en/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(
            value=None,
            source_url="https://fintel.io/i/virtus-family-office-llc",
            verification_method=(
                "13F shows ~$78M in reportable holdings, but 13F only captures certain "
                "US equity positions — not a reliable total-AUM figure, so left blank rather "
                "than presented as verified AUM"
            ),
            confidence=Confidence.NONE,
        ),
        hq_address="500 West Overland Suite 250-Q",
        hq_city="El Paso",
        hq_state="TX",
        hq_country="United States of America",
        domain="virtus-usa.com",
        website="https://virtus-usa.com/en/",
        corporate_linkedin=None,
        firm_email=SF(
            value="adminvfo@virtus-usa.com",
            source_url="https://virtus-usa.com/en/",
            verification_method="listed on official site; syntax + MX check passed",
            confidence=Confidence.HIGH,
        ),
        firm_phone=SF(
            value="+1 915 730 3885",
            source_url="https://virtus-usa.com/en/",
            verification_method="listed on official site; format/region check passed",
            confidence=Confidence.HIGH,
        ),
        classification=Classification.MFO,
        classification_evidence="Self-described on its own website as 'a multifamily office'.",
        classification_source_url="https://virtus-usa.com/en/",
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001913482",
        principals=[],
        signals=[],
        blind_spots=(
            "Could not verify AUM (site doesn't disclose; 13F undercounts). No named "
            "principals found on the homepage in this pass — leadership page not fetched."
        ),
    ),
    Firm(
        firm_id="pointone-family-office",
        name="PointOne Family Office, LLC",
        description=SF(
            value=(
                "Boutique multi-family office for ultra-high-net-worth families offering "
                "integrated investment management, curated private investments, estate "
                "planning, philanthropy, tax, governance, and concierge services."
            ),
            source_url="https://www.p1fo.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value=(
                "Aligned capital partnership and commercial participation for UHNW families "
                "with active business interests; operates three integrated platforms — P1FO "
                "(multi-family office advisory), P1S (investment banking for complex/special "
                "situations, noted expertise in sports), and P1P (principal investing/GP)."
            ),
            source_url="https://www.p1fo.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Sports and other non-traditional industries (via investment banking arm)",
            source_url="https://www.p1fo.com/",
            verification_method="first-party website",
            confidence=Confidence.MEDIUM,
        ),
        aum=SF(
            value="$327M",
            source_url="https://fintrx.com/firms/firm/pointone-family-office-338563",
            verification_method=(
                "Secondary source citing SEC Form ADV data (CRD 338563); primary IAPD firm "
                "page could not be directly fetched (JS-rendered)"
            ),
            confidence=Confidence.MEDIUM,
        ),
        hq_address="232 Manhattan Beach Blvd, Suite D",
        hq_city="Manhattan Beach",
        hq_state="CA",
        hq_country="United States of America",
        domain="p1fo.com",
        website="https://www.p1fo.com/",
        corporate_linkedin="https://www.linkedin.com/company/pointone-family-office",
        firm_email=SF(
            value="info@p1fo.com",
            source_url="https://www.p1fo.com/",
            verification_method="listed on official site; syntax + MX check passed",
            confidence=Confidence.HIGH,
        ),
        firm_phone=SF(
            value="+1 310 737 2637",
            source_url="https://www.p1fo.com/",
            verification_method="listed on official site; format/region check passed",
            confidence=Confidence.HIGH,
        ),
        classification=Classification.MFO,
        classification_evidence="Self-described as 'a boutique multi-family office' on its own site.",
        classification_source_url="https://www.p1fo.com/",
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0002102280",
        principals=[],
        signals=[],
        blind_spots=(
            "AUM sourced secondhand, not directly from SEC IAPD (page is JS-rendered and "
            "didn't return data via fetch) — flagged Medium not High confidence. One search "
            "snippet listed a different street address (919 Manhattan Ave Suite 101) than the "
            "firm's own site (232 Manhattan Beach Blvd) — used the first-party site address "
            "and noted the discrepancy rather than silently picking one. No named principals "
            "found — leadership page didn't render team names via fetch."
        ),
    ),
    Firm(
        firm_id="pathstone",
        name="Pathstone",
        description=SF(
            value=(
                "Multi-family office partnering with families and institutions of significant "
                "means across wealth management, family office operations, and institutional "
                "investment oversight."
            ),
            source_url="https://pathstone.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value=(
                "'Boutique + rigor' approach: open-architecture manager independence, "
                "customized implementation aligned to client values, global manager network "
                "access, and integrated risk intelligence."
            ),
            source_url="https://pathstone.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(
            value="$185B+ aggregate ($125B Pathstone Family Office LLC + $62B affiliates), as of 2025-12-31",
            source_url="https://pathstone.com/",
            verification_method=(
                "First-party site figure, corroborated by familywealthreport.com ('Now A $100 "
                "Billion MFO') and wealthmanagement.com merger coverage"
            ),
            confidence=Confidence.HIGH,
        ),
        hq_address="10 Sterling Blvd, Suite 402",
        hq_city="Englewood",
        hq_state="NJ",
        hq_country="United States of America",
        domain="pathstone.com",
        website="https://pathstone.com/",
        corporate_linkedin="https://www.linkedin.com/company/pathstone-family-office",
        classification=Classification.MFO,
        classification_evidence=(
            "Founded 2010 as, and continuously operated as, a multi-family office serving "
            "many UHNW families, foundations, and endowments — not one family's wealth. "
            "Included as an honest MFO despite 'family office' in the name and industry "
            "coverage sometimes calling it a leading 'family office' generically."
        ),
        classification_source_url="https://pathstone.com/",
        discovery_source="ProPublica Nonprofit Explorer (990)",
        discovery_url="https://projects.propublica.org/nonprofits/organizations/",
        principals=[
            Principal(
                first_name="Kelly",
                last_name="Maregni",
                full_name="Kelly Maregni",
                title="President",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[
            Signal(
                signal_type="fund_commitment",
                description="Merged with Hall Capital Partners, creating a combined RIA with "
                "~$100B AUM and ~$160B AUM+AUA.",
                signal_date=None,
                source_url="https://www.wealthmanagement.com/ria-news/pathstone-to-merge-with-hall-capital-to-create-100b-aum-firm",
                confidence=Confidence.HIGH,
            ),
            Signal(
                signal_type="hire",
                description="Mill Creek Capital Advisors joined Pathstone, expanding its "
                "Philadelphia-metro presence.",
                signal_date=None,
                source_url="https://pathstone.com/",
                confidence=Confidence.MEDIUM,
            ),
        ],
        blind_spots=(
            "Could not verify specific sector tilts. Discovery link (ProPublica linked entity) "
            "was indirect — connected to Pathstone via a third-party trust filing rather than "
            "Pathstone's own 990, since Pathstone the RIA itself doesn't file a 990; retained "
            "the SEC/press sourced firm data since the entity's identity is well corroborated."
        ),
    ),
    Firm(
        firm_id="geller-family-office-services",
        name="Geller & Company (Geller Family Office Services)",
        description=SF(
            value=(
                "Founded 1984 by Martin Geller; premier NYC-based multi-family office and "
                "strategic financial advisory offering personal CFO services, financial "
                "reporting/accounting, wealth management, and family office services to UHNW "
                "clients."
            ),
            source_url="https://www.businesswire.com/news/home/20250115069200/en/Corient-Acquires-Multi-Family-Office-Business-of-Geller-Expanding-U.S.-Wealth-Management-Presence-and-Deepening-Family-Office-Capabilities",
            verification_method="press release, corroborated by wealthmanagement.com coverage",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(
            value="$10.4B (assets under management and advisement, at time of Corient acquisition, Jan 2025)",
            source_url="https://www.businesswire.com/news/home/20250115069200/en/Corient-Acquires-Multi-Family-Office-Business-of-Geller-Expanding-U.S.-Wealth-Management-Presence-and-Deepening-Family-Office-Capabilities",
            verification_method="corroborated across businesswire.com and wealthmanagement.com",
            confidence=Confidence.HIGH,
        ),
        hq_address=None,
        hq_city="New York",
        hq_state="NY",
        hq_country="United States of America",
        domain=None,
        website=None,
        corporate_linkedin=None,
        classification=Classification.MFO,
        classification_evidence="Repeatedly and explicitly described in press as a 'multi-family office' since founding, serving many UHNW clients.",
        classification_source_url="https://www.businesswire.com/news/home/20250115069200/en/Corient-Acquires-Multi-Family-Office-Business-of-Geller-Expanding-U.S.-Wealth-Management-Presence-and-Deepening-Family-Office-Capabilities",
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001592557",
        principals=[
            Principal(
                first_name="Martin",
                last_name="Geller",
                full_name="Martin Geller",
                title="Founder (historical)",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[
            Signal(
                signal_type="news",
                description="Corient acquired Geller's multi-family office business "
                "(~$10.4B AUM/advisement), expanding Corient's wealth management presence.",
                signal_date="2025-01-15",
                source_url="https://www.businesswire.com/news/home/20250115069200/en/Corient-Acquires-Multi-Family-Office-Business-of-Geller-Expanding-U.S.-Wealth-Management-Presence-and-Deepening-Family-Office-Capabilities",
                confidence=Confidence.HIGH,
            )
        ],
        blind_spots=(
            "As of Jan 2025 the MFO business was acquired by Corient — could not verify "
            "whether 'Geller Family Office Services' still operates as a distinct branded "
            "entity today or has been fully absorbed. Could not verify a current domain "
            "(likely redirects to corient.com). No current (post-acquisition) principal names "
            "verified — Martin Geller listed as historical founder only."
        ),
    ),
    Firm(
        firm_id="white-knight-family-office",
        name="White Knight Family Office LLC",
        description=SF(confidence=Confidence.NONE),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(confidence=Confidence.NONE),
        hq_address=None,
        hq_city=None,
        hq_state=None,
        hq_country="United States of America",
        domain=None,
        website=None,
        corporate_linkedin=None,
        classification=Classification.UNKNOWN,
        classification_evidence=(
            "Appears in an SEC Form D filing and aggregator listings (CB Insights, "
            "WhoIsRaisingMoney) under a name containing 'Family Office,' but no first-party "
            "website was found and no credible secondary source affirmatively describes it as "
            "serving one family's wealth. State registration records conflict on address "
            "(Boca Raton, FL vs. Saint Louis, MO), suggesting possible confusion between "
            "similarly-named entities. Per the brief's rule, a name containing 'family office' "
            "is not itself qualifying evidence — classified Unable to Determine rather than "
            "guessed as SFO."
        ),
        classification_source_url=None,
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001809107",
        principals=[],
        signals=[],
        blind_spots=(
            "Could not verify description, thesis, sectors, AUM, HQ, or any principal. "
            "Address conflicts across public records were not resolved in this pass. This "
            "record illustrates the classification-honesty rule working as intended rather "
            "than a fully enriched record."
        ),
    ),
]


REJECTED_FIRMS: list[Firm] = [
    Firm(
        firm_id="point72-rejected",
        name="Point72",
        description=SF(
            value=(
                "Originated in 2014 as Steven A. Cohen's family office (successor to S.A.C. "
                "Capital Advisors), but converted to a registered investment adviser and began "
                "accepting outside capital on 2018-01-01."
            ),
            source_url="https://point72.com/",
            verification_method="first-party + press corroboration",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(confidence=Confidence.NONE),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(confidence=Confidence.NONE),
        hq_address=None,
        hq_city=None,
        hq_state=None,
        hq_country=None,
        domain="point72.com",
        website="https://point72.com/",
        corporate_linkedin=None,
        classification=Classification.UNKNOWN,
        classification_evidence=None,
        classification_source_url=None,
        discovery_source="SEC EDGAR Form D",
        discovery_url="https://www.sec.gov/Archives/edgar/data/0001465991",
        principals=[],
        signals=[],
        blind_spots=None,
        rejected_reason=(
            "Fails the firm-level qualifying rule as of this pass: Point72 now explicitly "
            "manages outside/third-party capital as a 1,650+ person registered investment "
            "adviser and multi-strategy manager, not exclusively one family's wealth. It "
            "originated as a family office, but current affirmative evidence shows it no "
            "longer fits the definition — per the brief's explicit instruction not to relabel "
            "a firm to make the dataset look more valuable, this is excluded from the "
            "qualifying set and logged here instead."
        ),
    )
]
