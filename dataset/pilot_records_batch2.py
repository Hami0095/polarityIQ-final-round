"""Batch 2: 5 more qualifying firms added specifically to fix source
concentration (work item 1) and demonstrate the additional discovery
channels + contact-sourcing techniques requested (work item 2), enriched
2026-07-25. Contact fields below were cross-checked against raw HTML
(not just the WebFetch summarizer — see DECISIONS.md for why that
mattered) before being included.
"""
from __future__ import annotations

from dataset.schema import Classification, Confidence, Firm, Principal, Signal, SourcedField

SF = SourcedField

BATCH2_FIRMS: list[Firm] = [
    Firm(
        firm_id="arsenault-family-office",
        name="Real Capital Solutions (Arsenault Family Office)",
        description=SF(
            value=(
                "Real estate investment and asset management platform built by Marcel "
                "Arsenault over 40+ years; formalized as the Arsenault family's family office "
                "structure. One of the most active private owners of commercial real estate "
                "in the western United States."
            ),
            source_url="https://www.fintrx.com/blog/family-office-real-estate-investment-activity-1h-2026?hs_amp=true",
            verification_method="press/industry-data source, corroborated by realcapitalsolutions.com",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Direct ownership of value-add and distressed commercial real estate, "
            "especially office, held long-term rather than through fund vehicles; ~$1B "
            "earmarked for distressed office buildings in 2025.",
            source_url="https://realcapitalsolutions.com/news/",
            verification_method="first-party site + press corroboration",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Commercial real estate (office, value-add, distressed)",
            source_url="https://realcapitalsolutions.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        aum=SF(
            value="~$5.12B across 395+ real estate investments (career total, not a point-in-time AUM figure)",
            source_url="https://theorg.com/org/real-capital-solutions/org-chart/marcel-arsenault",
            verification_method="corroborated across theorg.com and griinstitute.org bios",
            confidence=Confidence.MEDIUM,
        ),
        hq_city="Boulder",
        hq_state="CO",
        hq_country="United States of America",
        domain="realcapitalsolutions.com",
        website="https://realcapitalsolutions.com/",
        classification=Classification.SFO,
        classification_evidence=(
            "Industry data source (fintrx) explicitly labels this 'Real Capital Solutions "
            "(Arsenault Family Office)' and tracks its deals under that name; built and "
            "wholly controlled by Marcel Arsenault personally, not managing outside client "
            "capital."
        ),
        classification_source_url="https://www.fintrx.com/blog/family-office-real-estate-investment-activity-1h-2026?hs_amp=true",
        discovery_source="Deal/Transaction Press",
        discovery_url="https://www.fintrx.com/blog/family-office-real-estate-investment-activity-1h-2026?hs_amp=true",
        principals=[
            Principal(
                first_name="Marcel", last_name="Arsenault", full_name="Marcel Arsenault",
                title="Chairman, CEO & Founder",
                linkedin_url=SF(
                    value="https://www.linkedin.com/in/marcelrcs/",
                    source_url="https://realcapitalsolutions.com/team/",
                    verification_method="URL present verbatim in firm's own team-page HTML (checked raw source, not just summarized)",
                    confidence=Confidence.HIGH,
                ),
                work_email=SF(
                    confidence=Confidence.NONE,
                    verification_method="Site uses Cloudflare-obfuscated email display; real address not extractable without JS execution, which we did not attempt (would edge toward evading the site's anti-scraping protection)",
                ),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="Judy", last_name="Lawson", full_name="Judy Lawson",
                title="Chief Operating Officer",
                linkedin_url=SF(
                    value="https://www.linkedin.com/in/judy-lawson/",
                    source_url="https://realcapitalsolutions.com/team/",
                    verification_method="URL present verbatim in raw page HTML",
                    confidence=Confidence.HIGH,
                ),
                work_email=SF(confidence=Confidence.NONE, verification_method="Cloudflare-obfuscated on site, not extracted"),
                direct_phone=SF(
                    value="+1 303 533 1628",
                    source_url="https://realcapitalsolutions.com/team/",
                    verification_method="Plaintext in raw page HTML directly under her bio; format+region check passed",
                    confidence=Confidence.HIGH,
                ),
            ),
            Principal(
                first_name="Adam", last_name="Abeln", full_name="Adam Abeln",
                title="Chief Acquisitions Officer",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE, verification_method="Cloudflare-obfuscated on site, not extracted"),
                direct_phone=SF(
                    value="+1 305 433 0655",
                    source_url="https://realcapitalsolutions.com/team/",
                    verification_method="Plaintext in raw page HTML directly under his bio; format+region check passed",
                    confidence=Confidence.HIGH,
                ),
            ),
        ],
        signals=[
            Signal(
                signal_type="investment",
                description="Chairman Marcel Arsenault personally acquired and managed 395+ "
                "real estate investments totaling ~$5.12B over 40+ years; plans ~$1B into "
                "distressed office buildings in 2025.",
                source_url="https://theorg.com/org/real-capital-solutions/org-chart/marcel-arsenault",
                confidence=Confidence.MEDIUM,
            ),
        ],
        blind_spots=(
            "Contact fields: checked the firm's own /team/ page HTML directly (not just the "
            "WebFetch summary — the summarizer initially reported plausible-looking "
            "firstname@domain emails for every person that do NOT exist in the page's raw "
            "source; the real emails are Cloudflare-obfuscated and were correctly left blank "
            "instead of guessed or decoded). Phone numbers and LinkedIn URLs were verified "
            "present verbatim in the raw HTML and are used with confidence. Could not verify "
            "a current point-in-time AUM figure (the $5.12B figure is a career transaction "
            "total, not a snapshot AUM, so it's flagged Medium and labeled accordingly rather "
            "than presented as verified AUM)."
        ),
    ),
    Firm(
        firm_id="rock-gilbert-family-office",
        name="ROCK (Dan Gilbert Family Office / Rock Ventures)",
        description=SF(
            value=(
                "Single-family office headquartered in Detroit managing the fortune Dan "
                "Gilbert built through Quicken Loans/Rocket Companies, plus investments in "
                "real estate, professional sports, technology, and Detroit community "
                "development. Ties together 100+ entities in the 'Rock Family of Companies.'"
            ),
            source_url="https://altss.com/profile/rock-ventures-dan-gilbert-family-office",
            verification_method="industry-data profile, corroborated by rock.com and Yahoo Finance coverage",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Real estate is the core focus; also funds startups via Detroit Venture "
            "Partners and oversees investments through the family office structure.",
            source_url="https://finance.yahoo.com/news/detroit-billionaire-dan-gilbert-using-110000138.html",
            verification_method="press",
            confidence=Confidence.MEDIUM,
        ),
        sectors=SF(
            value="Real estate, professional sports, technology/startups, community development",
            source_url="https://finance.yahoo.com/news/detroit-billionaire-dan-gilbert-using-110000138.html",
            verification_method="press",
            confidence=Confidence.MEDIUM,
        ),
        aum=SF(confidence=Confidence.NONE),
        hq_city="Detroit",
        hq_state="MI",
        hq_country="United States of America",
        domain="rock.com",
        website="https://rock.com/",
        classification=Classification.SFO,
        classification_evidence=(
            "Explicitly described by an industry data profile as 'a single-family office' "
            "for the Gilbert family, and by the firm's own site language ('the Gilberts and "
            "the ... Family of Companies')."
        ),
        classification_source_url="https://altss.com/profile/rock-ventures-dan-gilbert-family-office",
        discovery_source="Regional Business Press",
        discovery_url="https://finance.yahoo.com/news/detroit-billionaire-dan-gilbert-using-110000138.html",
        principals=[
            Principal(
                first_name="Dan", last_name="Gilbert", full_name="Dan Gilbert",
                title="Founder",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            )
        ],
        signals=[
            Signal(
                signal_type="news",
                description="ROCK/Rock Ventures now employs ~70 people and operates from a "
                "50,000 sq ft space at One Campus Martius, Detroit, housing 90+ companies.",
                source_url="https://www.businesswire.com/news/home/20220503005192/en/Pophouse-Unveils-First-of-its-Kind-Office-Space-for-Rock-Ventures-and-the-Rock-Family-of-Companies",
                confidence=Confidence.MEDIUM,
            )
        ],
        blind_spots=(
            "No contact info found for Dan Gilbert or named ROCK staff in this pass — rock.com "
            "did not expose a plaintext phone or email in raw HTML (checked directly). Could "
            "not verify AUM."
        ),
    ),
    Firm(
        firm_id="pritzker-group-psp-partners",
        name="Pritzker Group / PSP Partners",
        description=SF(
            value=(
                "Chicago-based private investment firm(s) built on Pritzker family capital. "
                "PSP Partners was founded by Penny Pritzker (former U.S. Secretary of "
                "Commerce); Pritzker Group's buyout arm (Pritzker Private Capital) is chaired "
                "by Anthony (Tony) Pritzker. Deploys permanent, family-balance-sheet capital "
                "without outside LPs."
            ),
            source_url="https://www.psppartners.com/overview/",
            verification_method="first-party website, corroborated by Wikipedia bios of Penny and Anthony Pritzker",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Permanent-capital investing across established businesses (PSP Capital), "
            "high-growth technology (PSP Growth), and real estate (Pritzker Realty Group), "
            "without fund-life or LP redemption constraints.",
            source_url="https://www.psppartners.com/overview/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Diversified: established businesses/buyouts, growth technology, real estate",
            source_url="https://www.psppartners.com/overview/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        aum=SF(confidence=Confidence.NONE),
        hq_address="444 West Lake Street, Suite 3500",
        hq_city="Chicago",
        hq_state="IL",
        hq_country="United States of America",
        domain="psppartners.com",
        website="https://www.psppartners.com/",
        firm_phone=SF(
            value="+1 312 873 4800",
            source_url="https://www.psppartners.com/our-team/",
            verification_method="Plaintext in raw page HTML; format+region check passed",
            confidence=Confidence.HIGH,
        ),
        classification=Classification.SFO,
        classification_evidence=(
            "Industry profile (Altss) and Wikipedia both describe Pritzker Group as a single-"
            "family office deploying only Pritzker family balance-sheet capital, no outside "
            "LPs; PSP Partners' own site confirms Penny Pritzker as founder/chairman."
        ),
        classification_source_url="https://altss.com/profile/pritzker-group",
        discovery_source="University Donor/Foundation Bridge",
        discovery_url="https://www.chicagobooth.edu/media-relations-and-communications/press-releases/gift-from-anthony-pritzker-family-foundation-to-chicago-booth-family-office-initiative",
        principals=[
            Principal(
                first_name="Penny", last_name="Pritzker", full_name="Penny Pritzker",
                title="Founder and Chairman, PSP Partners",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="Anthony", last_name="Pritzker", full_name="Anthony Pritzker",
                title="Managing Partner, Pritzker Group; Chair, Pritzker Private Capital",
                linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE),
                direct_phone=SF(confidence=Confidence.NONE),
            ),
        ],
        signals=[
            Signal(
                signal_type="news",
                description="Anthony Pritzker Family Foundation gave $5M to the University of "
                "Chicago Booth School of Business to endow its Family Office Initiative "
                "faculty director position.",
                source_url="https://www.chicagobooth.edu/media-relations-and-communications/press-releases/gift-from-anthony-pritzker-family-foundation-to-chicago-booth-family-office-initiative",
                confidence=Confidence.HIGH,
            )
        ],
        blind_spots=(
            "Pritzker Group and PSP Partners are related but organizationally distinct "
            "Pritzker-family vehicles (Anthony's side vs. Penny's side respectively) — "
            "recorded together here since the discovery lead didn't cleanly separate them; "
            "flagging that these may need to be split into two records when scaling, with "
            "more research to confirm the actual corporate relationship. No direct contact "
            "found for either named principal. Could not verify AUM for either entity."
        ),
    ),
    Firm(
        firm_id="bln-capital",
        name="BLN Capital",
        description=SF(
            value=(
                "Berlin-based family office founded in 2021 by three Kolibri Games "
                "co-founders (Daniel Stammler, Janosch Kühn, Oliver Löffler) after selling "
                "75% of Kolibri Games to Ubisoft in 2020 for ~€120M. Self-funded, no outside "
                "investors."
            ),
            source_url="https://sifted.eu/articles/bln-capital-family-office",
            verification_method="press, corroborated by firm's own site",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Seed/pre-seed venture direct investments (€50k-€500k, ~15/year) in "
            "technology and gaming across Europe and the US, plus fund commitments "
            "(€200k-€2M each, up to €10M/year) to PE/VC funds globally.",
            source_url="https://www.blncapital.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(
            value="Technology, gaming",
            source_url="https://www.blncapital.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        aum=SF(confidence=Confidence.NONE),
        hq_city="Berlin",
        hq_country="Germany",
        domain="blncapital.com",
        website="https://www.blncapital.com/",
        firm_email=SF(
            value="info@blncapital.com",
            source_url="https://www.blncapital.com/",
            verification_method="Plaintext in raw page HTML; syntax+MX check passed",
            confidence=Confidence.HIGH,
        ),
        classification=Classification.SFO,
        classification_evidence=(
            "Press (Sifted) explicitly describes it as the personal family office of three "
            "named founders funded solely from their own liquidity event, with 'no outside "
            "investors.'"
        ),
        classification_source_url="https://sifted.eu/articles/bln-capital-family-office",
        discovery_source="Liquidity-Event Tracing",
        discovery_url="https://sifted.eu/articles/bln-capital-family-office",
        principals=[
            Principal(
                first_name="Daniel", last_name="Stammler", full_name="Daniel Stammler",
                title="Founder", linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE), direct_phone=SF(confidence=Confidence.NONE),
            ),
            Principal(
                first_name="Janosch", last_name="Kühn", full_name="Janosch Kühn",
                title="Founder", linkedin_url=SF(confidence=Confidence.NONE),
                work_email=SF(confidence=Confidence.NONE), direct_phone=SF(confidence=Confidence.NONE),
            ),
        ],
        signals=[
            Signal(
                signal_type="news",
                description="Founders sold 75% of Kolibri Games to Ubisoft in 2020 for ~€120M, "
                "left Kolibri in April 2021 to found BLN Capital.",
                source_url="https://sifted.eu/articles/bln-capital-family-office",
                confidence=Confidence.HIGH,
            )
        ],
        blind_spots=(
            "Could not verify AUM. Only a firm-level inbox is public (verified genuine in raw "
            "HTML); no direct principal email/phone found despite named founders being public "
            "figures via the Kolibri Games exit coverage."
        ),
    ),
    Firm(
        firm_id="bedrock-group",
        name="Bedrock Group",
        description=SF(
            value=(
                "Independent multi-family office and UHNW wealth manager founded in Geneva "
                "in 2004 by Ariel Arazi, Maurice Ephrati, and David Joory; offices in London, "
                "Geneva, and Monaco, managing wealth for 'a small circle of families and "
                "institutions.'"
            ),
            source_url="https://www.bedrockgroup.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        investment_thesis=SF(
            value="Portfolio management, private-market access, and family strategy/"
            "governance tailored to each client family's specific objectives.",
            source_url="https://www.bedrockgroup.com/",
            verification_method="first-party website",
            confidence=Confidence.HIGH,
        ),
        sectors=SF(confidence=Confidence.NONE),
        aum=SF(
            value="CHF 8.4B (~US$10.7B) in client assets",
            source_url="https://finance.yahoo.com/markets/stocks/articles/corient-continues-global-expansion-acquisition-083000867.html",
            verification_method="corroborated across citybiz.co and corient.com acquisition coverage",
            confidence=Confidence.HIGH,
        ),
        hq_address="4 Chemin des Vergers",
        hq_city="Geneva",
        hq_country="Switzerland",
        domain="bedrockgroup.com",
        website="https://www.bedrockgroup.com/",
        firm_email=SF(
            value="info@bedrockgroup.ch",
            source_url="https://www.bedrockgroup.com/",
            verification_method="listed on official site contact page; syntax check passed "
            "(MX check not run — see blind_spots)",
            confidence=Confidence.MEDIUM,
        ),
        firm_phone=SF(
            value="+41 22 592 54 55",
            source_url="https://www.bedrockgroup.com/",
            verification_method="listed on official site; format check passed (non-US region, "
            "lower confidence on the region-specific validity check than for US numbers)",
            confidence=Confidence.MEDIUM,
        ),
        classification=Classification.MFO,
        classification_evidence="Self-described as a 'multi-family office' since founding; "
        "won 'Best Multi-Family Office' at the 2026 Swiss WealthBriefing Awards.",
        classification_source_url="https://www.bedrockgroup.com/bedrock-group-named-best-multi-family-office-at-the-2026-swiss-wealthbriefing-awards/",
        discovery_source="Conference/Association Speaker List",
        discovery_url="https://lbs.eventscase.com/EN/FamilyBusinessConference2026",
        principals=[],
        signals=[
            Signal(
                signal_type="news",
                description="Corient agreed to acquire Bedrock Group, extending Corient's "
                "footprint into Geneva, London, Monaco, and Lisbon.",
                source_url="https://www.citybiz.co/article/833144/corient-to-acquire-geneva-based-bedrock-group-expanding-european-wealth-management-footprint/",
                confidence=Confidence.HIGH,
            )
        ],
        blind_spots=(
            "Discovered via a conference speaker bio (Carlota van de Koppel, Partner & COO at "
            "Bedrock Group, listed as a panelist) rather than the firm's own conference "
            "presence — a valid but indirect instance of the conference-discovery channel; "
            "flagging this so the channel's real yield isn't overstated. Did not verify the "
            "COO's individual contact info. Following the Corient acquisition (announced "
            "2026), unclear whether Bedrock will continue operating under its own brand — "
            "same caveat as the Geller record."
        ),
    ),
]
