"""Second-pass Wikidata enrichment for the 14 QIDs already in the qualifying set
(enrichment/wikidata_enrich.py) — those records are name/HQ/website only; this pulls the
remaining structured claims the initial pass never queried: P2403 (total assets), P2139
(revenue), P169 (CEO), P112 (founder), P571 (inception), P159 (HQ), P1128 (employees),
P856 (website), P17 (country). One SPARQL query for all 14 QIDs at once (cached to
data/interim/wikidata_details.json), plus an attempted Wikipedia REST summary fetch per
QID's enwiki sitelink for a real description/dated-event source.

Findings that shape what this module actually does (2026-07-26, confirmed before writing
anything, same standard as the ADV Schedule A confirm-before-writing step):
  - None of the 14 QIDs have P2403 (total assets), P2139 (revenue), or P1128 (employees) —
    checked directly, all three come back empty for every item. Nothing fabricated in
    their place; get_wikidata_details() simply won't produce keys for absent properties.
    If a firm-financial figure is ever found for any of these fields it must be labeled
    "Total assets (Wikidata P2403)" / "Revenue (Wikidata P2139)" — never written into an
    aum field, which is what the Cascade net-worth incident and the 13F refusal both
    established: a source-specific financial figure is not interchangeable with AUM.
  - None of the 14 QIDs have an English Wikipedia sitelink (checked via
    wbgetentities?props=sitelinks) — there is no Wikipedia article to pull a description
    or dated event from for any of them. This is a real, verified absence, not a fetch
    failure, and is recorded as such rather than silently skipped.
  - P169 (CEO) and P112 (founder) DO exist for a handful of items and are used to fill
    principal_1/2 name+title. P571 (inception) exists for several and is recorded as a
    dated "firm founded" signal, sourced to the Wikidata entity URL (Wikidata's own claim,
    not a Wikipedia article — labeled accordingly, not dressed up as press coverage).
  - Q113288804 ("166 2nd Financial Services") resolves its P169/P112 claims to Adam Neumann
    and Rebekah Neumann (the WeWork founders) — an unusual enough claim on a small, obscure
    item that it reads as plausible vandalism/a joke edit rather than a verified fact. Not
    fact-checked against a second source here (out of scope for this pass), but flagged
    explicitly in blind_spots so a reader doesn't take it as more solid than it is.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import requests

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "wikidata_details.json"
USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"

SPARQL = """
SELECT ?item ?assets ?revenue ?ceoLabel ?founderLabel ?inception ?hqLabel ?countryLabel ?employees ?website WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wdt:P2403 ?assets. }}
  OPTIONAL {{ ?item wdt:P2139 ?revenue. }}
  OPTIONAL {{ ?item wdt:P169 ?ceo. }}
  OPTIONAL {{ ?item wdt:P112 ?founder. }}
  OPTIONAL {{ ?item wdt:P571 ?inception. }}
  OPTIONAL {{ ?item wdt:P159 ?hq. }}
  OPTIONAL {{ ?item wdt:P17 ?country. }}
  OPTIONAL {{ ?item wdt:P1128 ?employees. }}
  OPTIONAL {{ ?item wdt:P856 ?website. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""


def fetch_details(qids: list[str]) -> dict[str, dict]:
    """One SPARQL query for all QIDs (VALUES clause), grouped back into a per-QID dict.
    Multi-valued properties (a firm can have >1 founder) become lists; results are
    cached to disk so re-running this module doesn't re-hit query.wikidata.org."""
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    values = " ".join(f"wd:{q}" for q in qids)
    resp = requests.get(
        "https://query.wikidata.org/sparql",
        params={"query": SPARQL.format(values=values), "format": "json"},
        headers={"User-Agent": USER_AGENT}, timeout=60,
    )
    resp.raise_for_status()
    bindings = resp.json()["results"]["bindings"]

    details: dict[str, dict] = {}
    for b in bindings:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        d = details.setdefault(qid, {
            "assets": None, "revenue": None, "ceo": None, "founders": [],
            "inception": None, "hq": None, "country": None, "employees": None, "website": None,
        })
        if "assets" in b:
            d["assets"] = b["assets"]["value"]
        if "revenue" in b:
            d["revenue"] = b["revenue"]["value"]
        if "ceoLabel" in b:
            d["ceo"] = b["ceoLabel"]["value"]
        if "founderLabel" in b and b["founderLabel"]["value"] not in d["founders"]:
            d["founders"].append(b["founderLabel"]["value"])
        if "inception" in b:
            d["inception"] = b["inception"]["value"]
        if "hqLabel" in b:
            d["hq"] = b["hqLabel"]["value"]
        if "countryLabel" in b:
            d["country"] = b["countryLabel"]["value"]
        if "employees" in b:
            d["employees"] = b["employees"]["value"]
        if "website" in b:
            d["website"] = b["website"]["value"]

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(details, indent=2), encoding="utf-8")
    return details


def get_enwiki_summary(qid: str) -> dict | None:
    """Fetches the linked Wikipedia article's REST summary, if an enwiki sitelink exists.
    Returns None (not a guess) if there's no sitelink at all — confirmed the case for all
    14 QIDs enriched by this module as of 2026-07-26."""
    r = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "ids": qid, "props": "sitelinks", "format": "json"},
        headers={"User-Agent": USER_AGENT}, timeout=30,
    )
    r.raise_for_status()
    sitelinks = r.json()["entities"][qid].get("sitelinks", {})
    enwiki = sitelinks.get("enwiki")
    if not enwiki:
        return None
    title = enwiki["title"].replace(" ", "_")
    resp = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
        headers={"User-Agent": USER_AGENT}, timeout=30,
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "extract": data.get("extract"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
    }


if __name__ == "__main__":
    import sys
    details = fetch_details(sys.argv[1:])
    for qid, d in details.items():
        print(qid, d)
