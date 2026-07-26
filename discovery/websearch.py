"""One search connector, used two ways: (1) as a discovery channel — run broad queries
("family office" + a city, "sold his company" + "family office", conference speaker lists — press,
deal, liquidity-event sourcing all go through the same search+classify-by-URL logic), and
(2) as the entity-resolution + enrichment step for a specific candidate name (e.g. an EDGAR
issuer) — does an operating firm distinct from the filing vehicle actually exist, and what does
its own site / press say about it.

No paid search API key is configured in this environment. Uses DuckDuckGo's HTML endpoint
(html.duckduckgo.com, POST) — no API key, no login, same kind of public search a person doing
this research by hand would see. This is a real, if fragile, network dependency: DuckDuckGo can
change this page's markup or rate-limit without notice, and this module has no fallback beyond
returning an empty result list (which is treated as "no evidence found," not an error to hide).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from dataset.classification import classify
from dataset.schema import Classification, Firm
from enrichment.extract import extract_with_llm
from enrichment.fetch import fetch
from enrichment.website_resolve import _page_matches_firm, merge_extracted_fields

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FamilyOfficeResearchProject/1.0 research-assessment@example.com"
SEARCH_URL = "https://html.duckduckgo.com/html/"

RESULT_RE = re.compile(r'result__a"\s+href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")

DIRECTORY_DOMAINS = {
    "familyofficehub.io", "altss.com", "linkedin.com", "facebook.com", "wikipedia.org",
    "pipelineroad.com", "bloomberg.com/profile", "crunchbase.com", "zoominfo.com",
    # 13F/ADV/AUM data aggregators — these republish a firm's name from regulatory filings
    # and will legitimately contain it, but they are not the firm's own site (confirmed
    # false-positive-shaped case: "Danis Family Office" -> aum13f.com, 2026-07-25).
    "aum13f.com", "whalewisdom.com", "adviserinfo.sec.gov", "sec.report", "fintrx.com",
    "advisorfacts.com", "getwarmer.com", "radientanalytics.com", "money.usnews.com",
    "eintaxid.com", "opencorporates.com", "bizapedia.com", "corporationwiki.com",
    "dnb.com", "bloomberg.com",
}
PRESS_DOMAINS_HINTS = [
    "businesswire.com", "prnewswire.com", "reuters.com", "bloomberg.com", "forbes.com",
    "wsj.com", "ft.com", "businessjournal", "businessjournals.com", "axios.com",
    "commercialobserver.com", "pehub.com", "institutionalinvestor.com",
]


@dataclass
class SearchResult:
    url: str
    title: str
    domain: str
    category: str  # "first_party" | "press" | "directory" | "unknown"


def _classify_url(url: str, firm_name_slug: str) -> str:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if any(d in domain for d in DIRECTORY_DOMAINS):
        return "directory"
    if any(hint in domain for hint in PRESS_DOMAINS_HINTS):
        return "press"
    # A domain that's a close textual match to the firm name is a plausible first-party site —
    # same slugging heuristic as enrichment/website_resolve.py, applied to real search hits
    # instead of a blind guess.
    domain_slug = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
    if firm_name_slug and (firm_name_slug in domain_slug or domain_slug in firm_name_slug):
        return "first_party"
    return "unknown"


class SearchBlocked(Exception):
    """Raised when DuckDuckGo's HTML endpoint returns its challenge/landing page instead of
    real results. Confirmed to happen under sustained use (2026-07-25): a run processing ~30
    candidates in quick succession got rate-limited partway through, and every subsequent
    request came back as a 202 landing page with zero result links — indistinguishable from
    "no results" unless checked for explicitly. Treating that silently as "no evidence found"
    would have caused a wave of false entity-resolution rejections for real firms (confirmed:
    PointOne Family Office, which resolves correctly to p1fo.com when DDG isn't rate-limiting,
    started coming back unresolved once blocking kicked in). Callers must NOT treat this the
    same as a genuine empty result."""


_last_request_at = 0.0
MIN_REQUEST_INTERVAL = 3.0  # seconds between requests to this endpoint, to reduce rate-limiting


def _throttle() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_at = time.monotonic()


MARGINALIA_URL = "https://old-search.marginalia.nu/search"
# Text-based-browser fallback of search.marginalia.nu (the default UI needs JS to render
# results client-side; this one serves static HTML). Different index than DDG — smaller,
# skews toward independent/small-business sites, doesn't reliably surface every well-known
# company (confirmed 2026-07-26: found real results for several test queries but missed
# pathstone.com specifically) — but it's a genuinely separate, keyless backend, which is the
# point: one provider being blocked shouldn't halt the pipeline.
_last_marginalia_at = 0.0
MARGINALIA_MIN_INTERVAL = 2.0


def _throttle_marginalia() -> None:
    global _last_marginalia_at
    elapsed = time.monotonic() - _last_marginalia_at
    if elapsed < MARGINALIA_MIN_INTERVAL:
        time.sleep(MARGINALIA_MIN_INTERVAL - elapsed)
    _last_marginalia_at = time.monotonic()


def _search_duckduckgo(query: str, max_results: int, timeout: int, retries: int) -> list[SearchResult] | None:
    """Returns None (not []) specifically to signal "blocked, try the fallback" — an actual
    empty real result set is still []. Only raises after both backends have been tried (see
    search())."""
    last_blocked = False
    resp = None
    for attempt in range(retries + 1):
        _throttle()
        try:
            resp = requests.post(SEARCH_URL, data={"q": query},
                                  headers={"User-Agent": USER_AGENT}, timeout=timeout)
        except requests.exceptions.RequestException:
            return []  # real network failure is "no evidence found," not something to fake around
        if resp.status_code == 200:
            last_blocked = False
            break
        last_blocked = True
        if attempt < retries:
            time.sleep(5 * (attempt + 1))  # back off harder each retry

    if last_blocked:
        return None

    firm_name_slug = re.sub(r"[^a-z0-9]", "", query.split(" family office")[0].split(" ")[0].lower())
    results = []
    for url, raw_title in RESULT_RE.findall(resp.text)[:max_results]:
        title = TAG_RE.sub("", raw_title).strip()
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        results.append(SearchResult(url=url, title=title, domain=domain,
                                     category=_classify_url(url, firm_name_slug)))
    return results


MARGINALIA_RESULT_RE = re.compile(
    r'<div class="url"><a[^>]*href="([^"]+)"[^>]*>.*?</a></div>\s*'
    r'<h2>\s*<a[^>]*>(.*?)</a>\s*</h2>\s*'
    r'<p class="description">(.*?)</p>',
    re.DOTALL,
)


def search_with_snippets(query: str, max_results: int = 10, timeout: int = 15) -> list[tuple[str, str, str]]:
    """Returns (url, title, snippet) tuples from Marginalia's result cards — snippet text is
    real, third-party-published description text about the result, useful as classification
    evidence in its own right (Evidence Class B), not just a means to find a URL to fetch
    further. DDG's HTML endpoint has snippets too but Marginalia's markup is simpler/more
    reliable to parse and DDG has been the one repeatedly blocked this session."""
    _throttle_marginalia()
    try:
        resp = requests.get(MARGINALIA_URL, params={"query": query},
                             headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except requests.exceptions.RequestException:
        return []
    if resp.status_code != 200:
        return []

    out = []
    for url, raw_title, raw_snippet in MARGINALIA_RESULT_RE.findall(resp.text)[:max_results]:
        title = TAG_RE.sub("", raw_title).strip()
        snippet = TAG_RE.sub("", raw_snippet).strip()
        out.append((url, title, snippet))
    return out


def _search_marginalia(query: str, max_results: int, timeout: int) -> list[SearchResult] | None:
    _throttle_marginalia()
    try:
        resp = requests.get(MARGINALIA_URL, params={"query": query},
                             headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except requests.exceptions.RequestException:
        return None
    if resp.status_code != 200:
        return None

    firm_name_slug = re.sub(r"[^a-z0-9]", "", query.split(" family office")[0].split(" ")[0].lower())
    urls = re.findall(r'href="(https?://[^"]+)"', resp.text)
    seen = set()
    results = []
    for url in urls:
        if "marginalia" in url or url in seen:
            continue
        seen.add(url)
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        results.append(SearchResult(url=url, title="", domain=domain,
                                     category=_classify_url(url, firm_name_slug)))
        if len(results) >= max_results:
            break
    return results


def search(query: str, max_results: int = 10, timeout: int = 15, retries: int = 2) -> list[SearchResult]:
    """Tries DuckDuckGo first; if it's blocked (not just empty — see SearchBlocked), falls
    back to Marginalia before giving up. Raises SearchBlocked only if BOTH backends are
    unavailable — a single provider being rate-limited should not halt the whole pipeline
    (2026-07-26: DDG got blocked mid-run three times in one session; Marginalia was added
    specifically so that stops being a hard stop)."""
    ddg_results = _search_duckduckgo(query, max_results, timeout, retries)
    if ddg_results is not None:
        return ddg_results

    marginalia_results = _search_marginalia(query, max_results, timeout)
    if marginalia_results is not None:
        return marginalia_results

    raise SearchBlocked(
        f"Both DuckDuckGo and Marginalia were unavailable/blocked for query {query!r} "
        f"after retries."
    )


def classify_from_search_snippets(name: str, hq_city: str | None = None) -> dict | None:
    """Evidence Class B (2026-07-26): a search result's own title+snippet is third-party
    published description text, usable as classification evidence directly — no website
    resolution or fetch required. Requires the firm NAME and a classification phrase to
    co-occur in the SAME result (not just anywhere across the result set), so this can't be
    fooled by an unrelated result that happens to mention "multi-family office" elsewhere.
    Returns a dict with classification/evidence_span/source_url, or None if nothing
    qualifying was found. Uses the SAME classify() phrase list/word-boundary logic as every
    other evidence path — no second, looser mechanism."""
    from dataset.classification import classify
    from dataset.schema import Classification

    query = f'"{name}" family office' + (f" {hq_city}" if hq_city else "")
    try:
        results = search_with_snippets(query)
    except SearchBlocked:
        return None

    name_tokens = [t for t in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split() if len(t) > 2]
    if not name_tokens:
        return None

    for url, title, snippet in results:
        combined = f"{title} {snippet}"
        combined_lower = combined.lower()
        # require at least the first 2 significant name tokens (or all, if fewer) present —
        # cheap proxy for "this result is actually about the candidate," not just any hit
        needed = name_tokens[:2] if len(name_tokens) >= 2 else name_tokens
        if not all(tok in combined_lower for tok in needed):
            continue
        result = classify(combined)
        if result.classification != Classification.UNKNOWN:
            return {
                "classification": result.classification,
                "evidence_span": result.evidence_span,
                "evidence": result.evidence,
                "source_url": url,
            }
    return None


def resolve_entity(candidate_name: str, hq_city: str | None = None, max_checked: int = 4) -> SearchResult | None:
    """Entity resolution: given a name (possibly a Form D filing vehicle), determine whether a
    distinct operating firm exists. A candidate that can't be resolved to an operating entity
    should be rejected, not shipped under the filing vehicle's name (per the explicit
    instruction). Returns the first search result that's neither a directory nor a press
    domain AND whose actual fetched content matches the firm name — slug-matching alone
    missed real cases (e.g. "PointOne Family Office" -> the real p1fo.com, no textual
    resemblance to the name), so this reuses website_resolve.py's content-verification check
    (_page_matches_firm) rather than trusting the domain string."""
    query = f'"{candidate_name}" family office'
    if hq_city:
        query += f" {hq_city}"
    results = search(query)
    candidates = [r for r in results if r.category in ("first_party", "unknown")][:max_checked]

    for candidate in candidates:
        try:
            page = fetch(candidate.url)
        except Exception:
            continue
        if _page_matches_firm(candidate_name, page.text):
            return candidate
    return None


def _classify_from_raw_page(firm: Firm, page) -> None:
    """Phrase classification against the RAW fetched page text, not just whatever the LLM
    extraction step happened to pull out as a "description" — see the same fix and rationale
    in enrichment/website_resolve.py:enrich_website_for_firm() (2026-07-26 diagnostic: real
    pages carry far more usable text than the LLM extraction step was surfacing). Only sets
    classification if not already decided, so a page found later doesn't overwrite one found
    earlier in the same enrichment pass."""
    if firm.classification != Classification.UNKNOWN:
        return
    result = classify(page.text)
    if result.classification != Classification.UNKNOWN:
        firm.classification = result.classification
        firm.classification_evidence = result.evidence
        firm.classification_source_url = page.url


def enrich_candidate_via_search(firm: Firm, max_press: int = 3) -> tuple[Firm, bool]:
    """Runs entity resolution for firm.name, then fetches the resolved first-party site's
    homepage + /about, /team, /leadership subpaths plus up to `max_press` press hits,
    extracting fields from each (evidence-span gated, same extract_with_llm() as the
    website-guess path) and merging via the SAME merge_extracted_fields() policy website_resolve
    uses — deterministic fields never get overwritten, first found wins otherwise.

    Returns (firm, resolved: bool). resolved=False means entity resolution found no operating
    site distinct from the filing vehicle — per the explicit instruction, the caller must treat
    this as a rejection candidate, not ship the record under the filing vehicle's name."""
    resolved = resolve_entity(firm.name, firm.hq_city)
    results = search(f'"{firm.name}" family office' + (f" {firm.hq_city}" if firm.hq_city else ""))
    press_hits = [r for r in results if r.category == "press"][:max_press]

    filled_all: list[str] = []
    sources_tried: list[str] = []

    if resolved:
        firm.website = firm.website or resolved.url
        firm.domain = firm.domain or urlparse(resolved.url).netloc.removeprefix("www.")
        for path in ("", "about/", "team/", "leadership/"):
            url = resolved.url.rstrip("/") + "/" + path
            try:
                page = fetch(url)
            except Exception:
                continue
            sources_tried.append(url)
            extracted = extract_with_llm(page.text, page.url, page.fetched_at)
            filled_all += merge_extracted_fields(firm, extracted)
            _classify_from_raw_page(firm, page)
            time.sleep(0.2)

    for hit in press_hits:
        try:
            page = fetch(hit.url)
        except Exception:
            continue
        sources_tried.append(hit.url)
        extracted = extract_with_llm(page.text, page.url, page.fetched_at)
        filled_all += merge_extracted_fields(firm, extracted)
        _classify_from_raw_page(firm, page)
        time.sleep(0.2)

    filled_desc = ", ".join(dict.fromkeys(filled_all)) if filled_all else "nothing"
    note = (f"Web search entity resolution: resolved={resolved.url if resolved else 'NONE'}; "
            f"{len(sources_tried)} source(s) fetched; filled: {filled_desc}.")
    firm.blind_spots = (firm.blind_spots or "") + " " + note
    return firm, resolved is not None
