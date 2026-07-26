"""Form 13F-HR cover-page parser. Every 13F-HR filing's cover page names a real person
signing on behalf of the reporting manager, with their title and direct phone — structured
regulatory data this project hasn't tapped yet for the 13F discovery channel (previously only
name+CIK were captured, see enrichment/edgar_13f_enrich.py's own docstring).

Two formats, both handled:
  - Modern (~2004+): a real `primaryDoc.xml` under
    sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/primary_doc.xml, with
    <coverPage><filingManager><name>/<address>, <form13FFileNumber>, and a
    <signatureBlock><name>/<title>/<phone>/<signatureDate>. Confirmed directly against a live
    filing (Boston Family Office LLC, CIK 1039807, accession 0001039807-26-000004) before
    writing the parser.
  - Older plain-text filings: the full submission .txt file has an unstructured cover-page
    block using literal "NAME:"/"TITLE:"/"PHONE:" labels (see PROJECT_BRIEF.md's own quoted
    example) inside the SEC-HEADER/text of the filing. Parsed with a tolerant line-based regex
    since there's no schema to rely on.

evidence_span is the literal filing text (the XML element text or the matched text block);
source is the concrete filing document URL, not a guessed one.
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
SUBMISSIONS_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "interim" / "edgar_13f_cache"

NS = {"n1": "http://www.sec.gov/edgar/thirteenffiler", "com": "http://www.sec.gov/edgar/common"}


def _cached_get(url: str, cache_key: str) -> str | None:
    SUBMISSIONS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = SUBMISSIONS_CACHE_DIR / cache_key
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8", errors="replace")
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    if resp.status_code != 200:
        return None
    cache_path.write_text(resp.text, encoding="utf-8", errors="replace")
    return resp.text


def latest_13f_hr_filing(cik: str) -> dict | None:
    """Most recent 13F-HR filing's accession number, primary document, filing date, and
    report (period) date, from EDGAR's own submissions API — no full-index re-parse needed."""
    cik_padded = f"{int(cik):010d}"
    text = _cached_get(
        f"https://data.sec.gov/submissions/CIK{cik_padded}.json", f"sub_{cik_padded}.json"
    )
    if not text:
        return None
    import json
    data = json.loads(text)
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    for i, form in enumerate(forms):
        if form.startswith("13F-HR"):
            return {
                "accession": recent["accessionNumber"][i],
                "primary_document": recent["primaryDocument"][i],
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
            }
    return None


def _parse_xml_cover(xml_text: str, source_url: str) -> dict | None:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    def find(path: str, node=root) -> str | None:
        el = node.find(path, NS)
        return el.text.strip() if el is not None and el.text else None

    filing_manager = root.find(".//n1:coverPage/n1:filingManager", NS)
    if filing_manager is None:
        return None
    name = find("n1:name", filing_manager)
    addr = filing_manager.find("n1:address", NS)
    city = find("com:city", addr) if addr is not None else None
    state = find("com:stateOrCountry", addr) if addr is not None else None
    street1 = find("com:street1", addr) if addr is not None else None

    file_number = find(".//n1:coverPage/n1:form13FFileNumber")

    sig = root.find(".//n1:signatureBlock", NS)
    signer_name = find("n1:name", sig) if sig is not None else None
    signer_title = find("n1:title", sig) if sig is not None else None
    signer_phone = find("n1:phone", sig) if sig is not None else None
    signature_date = find("n1:signatureDate", sig) if sig is not None else None

    if not name:
        return None
    return {
        "filer_name": name, "hq_city": city, "hq_state": state, "hq_street": street1,
        "file_number": file_number,
        "signer_name": signer_name, "signer_title": signer_title, "signer_phone": signer_phone,
        "signature_date": signature_date,
        "source_url": source_url,
        "evidence_span": xml_text[:4000],
    }


_TXT_COVER_RE = re.compile(
    r"NAME:\s*(?P<filer_name>.+?)\n"
    r"ADDRESS:\s*(?P<addr>.+?)\n"
    r".*?FORM 13F FILE NUMBER:\s*(?P<file_number>[\d\-]+)"
    r".*?PERSON SIGNING.*?\n"
    r"NAME:\s*(?P<signer_name>.+?)\n"
    r"TITLE:\s*(?P<signer_title>.+?)\n"
    r"PHONE:\s*(?P<signer_phone>[\d()\-\s]+)",
    re.DOTALL | re.IGNORECASE,
)


def _parse_txt_cover(txt: str, source_url: str) -> dict | None:
    m = _TXT_COVER_RE.search(txt)
    if not m:
        return None
    return {
        "filer_name": m.group("filer_name").strip(),
        "hq_city": None, "hq_state": None, "hq_street": None,
        "file_number": m.group("file_number").strip(),
        "signer_name": m.group("signer_name").strip(),
        "signer_title": m.group("signer_title").strip(),
        "signer_phone": m.group("signer_phone").strip(),
        "signature_date": None,
        "source_url": source_url,
        "evidence_span": m.group(0)[:4000],
    }


def get_cover_page(cik: str) -> dict | None:
    """Returns the parsed cover page for a CIK's most recent 13F-HR, or None if there is no
    13F-HR filing or neither parse format matches (left blank, not guessed)."""
    filing = latest_13f_hr_filing(cik)
    if not filing:
        return None
    cik_int = int(cik)
    accn_nodash = filing["accession"].replace("-", "")

    # EDGAR's submissions API returns primaryDocument as e.g. "xslForm13F_X02/primary_doc.xml"
    # (the styled-HTML rendering path) — confirmed 2026-07-26 that fetching that path returns
    # an XSL-transformed HTML wrapper, not raw XML. The actual raw XML sits at the same
    # filename directly under the accession folder, no subdirectory.
    primary_doc_filename = filing["primary_document"].rsplit("/", 1)[-1]
    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn_nodash}/{primary_doc_filename}"
    if primary_doc_filename.endswith(".xml"):
        xml_text = _cached_get(xml_url, f"{cik_int}_{accn_nodash}_primary.xml")
        if xml_text:
            parsed = _parse_xml_cover(xml_text, xml_url)
            if parsed:
                parsed["filing_date"] = filing["filing_date"]
                parsed["report_date"] = filing["report_date"]
                return parsed

    # Fallback: older plain-text full submission file
    txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{filing['accession']}.txt"
    txt = _cached_get(txt_url, f"{cik_int}_{accn_nodash}_full.txt")
    if txt:
        parsed = _parse_txt_cover(txt, txt_url)
        if parsed:
            parsed["filing_date"] = filing["filing_date"]
            parsed["report_date"] = filing["report_date"]
            return parsed
    return None


if __name__ == "__main__":
    import sys
    for cik in sys.argv[1:]:
        print(cik, get_cover_page(cik))
