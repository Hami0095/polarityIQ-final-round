"""Guess a firm's own website from its name, verify the guess against the
fetched page itself (not just "the request didn't 404"), and if it checks
out, run it through the generic LLM extraction path to fill in whatever the
deterministic EDGAR/ProPublica enrichers can't (description, thesis,
sectors, aum, additional contact fields).

This is deliberately a guess-and-verify step, not a search-engine lookup —
no web search API is wired in. It will miss plenty of real websites (firms
with names that don't map cleanly to a domain, sites on unusual TLDs,
firms with no first-party site at all) and that's a stated limitation, not
a hidden one: see resolve_website()'s return value and blind_spots wiring
in enrich_website_for_firm().
"""
from __future__ import annotations

import re

import requests
from rapidfuzz import fuzz

from dataset.classification import classify
from dataset.schema import Classification, Confidence, Firm
from enrichment.extract import extract_with_llm
from enrichment.fetch import fetch

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"

LEGAL_SUFFIXES = re.compile(
    r"\b(l\.?l\.?c\.?|l\.?p\.?|inc\.?|incorporated|corp\.?|corporation|ltd\.?|limited|"
    r"family office(s)?|family partners?|holdings?|group|capital|partners?|trust|"
    r"co\.?|company|ventures?|advisors?|management)\b",
    re.IGNORECASE,
)
# Generic corporate suffixes only — deliberately does NOT strip "family office" itself.
# Added 2026-07-26: the 13F backlog surfaced that roughly half of real "___ Family Office"
# domains keep the phrase verbatim (e.g. Hampshire Family Office's real site is
# hampshirefamilyoffice.com, confirmed via its ADV bulk 'Website Address' field) — the
# original LEGAL_SUFFIXES-based slug alone was stripping "family office" and guessing a
# generic, wrong domain (e.g. "boston.com" for Boston Family Office LLC) for every single one
# of the 68 13F candidates checked, a real bug this project just hadn't exercised before
# since the ADV/Wikidata channels always had a known website already and never hit this guess
# path for a family-office-named firm.
_CORPORATE_SUFFIXES_ONLY = re.compile(
    r"\b(l\.?l\.?c\.?|l\.?p\.?|inc\.?|incorporated|corp\.?|corporation|ltd\.?|limited)\b",
    re.IGNORECASE,
)


def _slug_keep_family_office(name: str) -> str:
    stripped = _CORPORATE_SUFFIXES_ONLY.sub(" ", name)
    stripped = re.sub(r"[^a-zA-Z0-9]+", "", stripped)
    return stripped.lower()

TLDS = [".com", ".net", ".org"]

NAME_MATCH_THRESHOLD = 85  # fuzz.partial_ratio of full firm name vs page title/text

FAMILY_OFFICE_MARKERS = [
    "family office", "family partners", "wealth management", "wealth advisors",
    "private wealth", "family wealth", "multi-family office", "single family office",
]


def _slug(name: str) -> str:
    stripped = LEGAL_SUFFIXES.sub(" ", name)
    stripped = re.sub(r"[^a-zA-Z0-9]+", "", stripped)
    return stripped.lower()


def candidate_domains(name: str) -> list[str]:
    slugs = dict.fromkeys([_slug(name), _slug_keep_family_office(name)])  # de-dup, keep order
    domains = []
    for slug in slugs:
        if not slug:
            continue
        domains += [f"{slug}{tld}" for tld in TLDS]
    return domains


def _page_matches_firm(name: str, page_text: str) -> bool:
    """Confirmed false-positive case (2026-07-25): a domain guess for
    "PointOne Family Office, LLC" landed on pointone.com, an unrelated AI
    billing startup, because a loose partial_ratio substring match on the
    brand word alone ("PointOne") scored above a 55-point threshold — a
    single brand word is enough to pass partial_ratio against almost any
    page that happens to use it. (token_set_ratio was tried as a fix but
    degrades badly comparing a short name against a long HTML blob — not
    the right tool either.) Two independent corrections instead: (1)
    raise partial_ratio's own bar substantially (55 -> 85); (2) require a
    second, different signal — if the firm's own name contains a
    family-office-flavored marker ("family office", "wealth management",
    etc.), the fetched page must contain a matching marker too. A page
    that's obviously a different business (here: "uses AI to passively
    track time and review bills") won't have one, and this check alone
    would have caught the PointOne case even before the threshold change."""
    head = page_text[:3000].lower()
    name_lower = name.lower()

    name_score = fuzz.partial_ratio(name_lower, head)
    if name_score < NAME_MATCH_THRESHOLD:
        return False

    name_markers = [m for m in FAMILY_OFFICE_MARKERS if m in name_lower]
    if name_markers and not any(m in head or m in page_text.lower() for m in name_markers):
        return False

    return True


def resolve_website(name: str, timeout: int = 8) -> str | None:
    """Try each candidate domain; return the first URL whose fetched page
    plausibly matches the firm name. None if nothing checked out — a miss
    here is a real "could not verify," not a fallback to guessing further."""
    for domain in candidate_domains(name):
        for scheme in ("https://", "http://"):
            url = f"{scheme}{domain}/"
            try:
                resp = requests.get(url, headers={"User-Agent": USER_AGENT},
                                     timeout=timeout, allow_redirects=True)
            except requests.exceptions.RequestException:
                continue
            if resp.status_code != 200:
                continue
            if _page_matches_firm(name, resp.text):
                return url
    return None


def merge_extracted_fields(firm: Firm, extracted: dict) -> list[str]:
    """Merge LLM-extracted fields into a Firm, filling ONLY fields that are currently
    blank — a deterministic source (regulatory filing) always outranks anything guessed or
    searched. Shared by enrich_website_for_firm() and discovery/websearch.py's search-based
    enrichment path, so there is exactly one merge policy, not two."""
    filled = []
    for field_name in ("description", "investment_thesis", "sectors", "aum", "firm_email", "firm_phone"):
        current = getattr(firm, field_name)
        new_field = extracted.get(field_name)
        if current.value is None and new_field is not None and new_field.value is not None:
            setattr(firm, field_name, new_field)
            filled.append(field_name)

    for hq_field in ("hq_city", "hq_state", "hq_country"):
        new_field = extracted.get(hq_field)
        if new_field and new_field.value and not getattr(firm, hq_field):
            setattr(firm, hq_field, new_field.value)
            filled.append(hq_field)
    return filled


def enrich_website_for_firm(firm: Firm, model: str | None = None) -> Firm:
    """Fetch+extract from the firm's website to fill any of
    description/investment_thesis/sectors/aum/hq_*/firm_email/firm_phone
    that the firm doesn't already have from a deterministic source. Never
    overwrites a field that's already set — deterministic sources
    (regulatory filings) outrank anything guessed or extracted here.

    If firm.website is ALREADY known (e.g. from ADV bulk data's own
    'Website Address' field, or a Wikidata P856 claim) it is used directly —
    domain-guessing from the name is only a fallback for candidates with no
    known website. Re-guessing a domain from the name when a real website
    is already on file was a real, fixed bug (2026-07-26): it wasted a
    guess-and-verify pass and, worse, meant a firm's own filed website was
    never actually fetched for extraction at all, silently leaving real
    yield on the table for exactly the candidates (ADV, Wikidata) that
    should have been the easiest to enrich."""
    if firm.website:
        url = firm.website
        note = "Using known website (already on file, not guessed): "
    else:
        url = resolve_website(firm.name)
        note = f"Website domain guess: tried {candidate_domains(firm.name)}; "
        if url is None:
            firm.blind_spots = (firm.blind_spots or "") + " " + note + "none matched the firm name, no website enrichment run."
            return firm

    firm.website = firm.website or url
    firm.domain = firm.domain or url.split("//", 1)[-1].split("/", 1)[0]

    # Homepages are frequently just a nav/title shell (confirmed 2026-07-26: several real,
    # successfully-fetched homepages yielded a "description" that was only the page title,
    # e.g. "Home - Element Pointe Family Office" — real text, correctly evidence-verified, but
    # not substantive enough to carry the affirmative single/multi-family language
    # classification needs). Try /about-style subpaths too, same as the search-based path in
    # discovery/websearch.py already does, stopping once a real description is found.
    kwargs = {"model": model} if model else {}
    filled_all: list[str] = []
    fetched_urls = []
    classified_here = False
    for path in ("", "about/", "about-us/", "who-we-are/", "team/", "firm/", "our-firm/"):
        if firm.description.value and classified_here:
            break
        page_url = url.rstrip("/") + "/" + path if path else url
        try:
            result = fetch(page_url)
        except Exception:
            continue
        fetched_urls.append(page_url)
        extracted = extract_with_llm(result.text, result.url, result.fetched_at, **kwargs)
        filled_all += merge_extracted_fields(firm, extracted)

        # Phrase classification against the RAW fetched page text directly, not just the
        # LLM-extracted description. Diagnostic (2026-07-26): real fetched pages have a median
        # of ~3KB of real text, but the LLM-extracted "description" value is only ~35 chars
        # median (a title fragment) — the affirmative "single-family office"/"multi-family
        # office" language a real page carries was reliably getting dropped by extraction
        # before classification ever saw it. dataset.classification.classify() already derives
        # a windowed evidence_span from whatever text it's given — it just needed to be run
        # against the real page text directly instead of only the sparse extracted field.
        # Confirmed working: arrowrootfamilyoffice.com's raw text contains "Multi Family
        # Office Services" and real prose describing service to "affluent families" that the
        # LLM extraction step never surfaced as a usable description.
        if firm.classification == Classification.UNKNOWN:
            page_result = classify(result.text, firm_name=firm.name)
            if page_result.classification != Classification.UNKNOWN:
                firm.classification = page_result.classification
                firm.classification_evidence = page_result.evidence
                firm.classification_source_url = result.url
                classified_here = True

    if not fetched_urls:
        firm.blind_spots = (firm.blind_spots or "") + " " + note + f"matched {url} but re-fetch for extraction failed."
        return firm

    filled_desc = ", ".join(dict.fromkeys(filled_all)) if filled_all else "nothing (page(s) matched but had no extractable/evidence-supported fields)"
    firm.blind_spots = (firm.blind_spots or "") + " " + note + f"fetched {len(fetched_urls)} page(s) at {url}, LLM extraction filled: {filled_desc}."
    return firm
