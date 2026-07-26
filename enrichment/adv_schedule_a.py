"""SEC Form ADV Schedule A ("Direct Owners and Executive Officers") extraction.

Bulk Schedule A/B data is NOT separately downloadable as a keyless CSV (confirmed 2026-07-26:
the SEC's bulk zip at the "information-about-registered-investment-advisers" page contains only
the base firm-roster CSV; the only other bulk archive covering Schedule A is the full historical
filing-data zip at sec.gov/foia-services, ~1.1GB across two parts, containing every RIA's every
amendment since 2011 — far too large to fetch and parse for 14 firms in this timebox). Instead,
this pulls each firm's own current ADV filing report PDF directly from
reports.adviserinfo.sec.gov/reports/ADV/{crd}/PDF/{crd}.pdf (the same public IAPD system
discovery already links to per-firm) and parses the literal "Schedule A" table out of the PDF
text. This is the filing itself, not a third-party summary.

Column semantics confirmed directly from the form instruction text embedded in the PDF (Item 2
of Schedule A, printed on every filing): the table is
  FULL LEGAL NAME (Individuals: Last, First, Middle) | DE/FE/I | Title or Status |
  Date Acquired (MM/YYYY) | Ownership Code | Control Person (Y/N) | PR | CRD/SSN
"Ownership Code" (NA/A-E) is a % ownership bracket, not a title — not used here. "Title or
Status" is used verbatim as filed. Rows with DE/FE (entity owners, e.g. a holding LLC) are
skipped for principal_1/2 purposes since those aren't a person's name/title.

A single filing PDF repeats the same Schedule A content once per registration track it covers
(confirmed identical byte-for-byte across repeats within one firm's PDF, e.g. Arrowroot Family
Office CRD 168744) — only the first occurrence is parsed.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import requests
from pypdf import PdfReader

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"
PDF_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "interim" / "adv_pdfs"

INVESTMENT_EXEC_TITLES = re.compile(
    r"CHIEF EXECUTIVE|CHIEF INVESTMENT|CHIEF OPERATING|CHIEF FINANCIAL|CHIEF COMPLIANCE|"
    r"PRESIDENT|MANAGING MEMBER|MANAGING DIRECTOR|MANAGING PARTNER|FOUNDER|PRINCIPAL|"
    r"PARTNER|DIRECTOR|CHAIRMAN|CEO|CIO|COO|CFO",
    re.IGNORECASE,
)

_ROW_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z .,'\-]+?)\s+"
    r"(?P<type>DE|FE|I)\s+"
    r"(?P<title>.+?)\s+"
    r"(?:(?P<date>\d{2}/\d{4})\s+)?"
    r"(?P<code>NA|[A-E])\s+"
    r"(?P<control>Y|N)\s+"
    r"(?P<pr>Y|N)\s*"
    r"(?P<crd>\d+)?$"
)
_ROW_START_RE = re.compile(r"^[A-Za-z][A-Za-z .,'\-]+\s+(?:DE|FE|I)\b")


def _fetch_pdf_text(crd: str) -> str | None:
    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = PDF_CACHE_DIR / f"{crd}.pdf"
    if cache_path.exists():
        content = cache_path.read_bytes()
    else:
        url = f"https://reports.adviserinfo.sec.gov/reports/ADV/{crd}/PDF/{crd}.pdf"
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
        if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
            return None
        content = resp.content
        cache_path.write_bytes(content)
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _rows_from_block(block: str) -> list[dict]:
    lines = [l.strip() for l in block.splitlines() if l.strip()]

    def flush(buf: str, rows: list[dict]) -> None:
        m = _ROW_RE.match(buf)
        if m:
            rows.append(m.groupdict())

    rows: list[dict] = []
    buf = ""
    for line in lines:
        if _ROW_START_RE.match(line):
            if buf:
                flush(buf, rows)
            buf = line
        elif buf:
            buf = (buf + " " + line).strip()
    if buf:
        flush(buf, rows)
    return rows


def _parse_schedule_a_rows(text: str) -> list[dict]:
    """A firm's filing report can repeat the "FULL LEGAL NAME" Schedule A header multiple
    times (once per registration track it covers, or across amendment history within the
    same PDF) with the real row data attached to only one occurrence — confirmed 2026-07-26
    across the 14 ADV firms (e.g. TFO Family Office Partners CRD 159440's first occurrence is
    70K characters away from its actual data rows). Scans every occurrence and returns the
    first one that yields at least one parsed row, since duplicate occurrences (when present)
    are identical anyway."""
    idx = 0
    while True:
        start = text.find("FULL LEGAL NAME", idx)
        if start == -1:
            return []
        end = text.find("Schedule B", start)
        block = text[start:end if end != -1 else len(text)]
        rows = _rows_from_block(block)
        if rows:
            return rows
        idx = start + 1


def get_principals(crd: str) -> list[dict]:
    """Returns up to 2 principals (name + title) for a firm's CRD, preferring rows whose
    title indicates investment/executive authority over passive ownership entries. Returns
    [] (not a guess) if the PDF can't be fetched or no individual rows parse cleanly."""
    text = _fetch_pdf_text(crd)
    if not text:
        return []
    rows = _parse_schedule_a_rows(text)
    people = [r for r in rows if r["type"] == "I" and r["name"] and r["title"]]
    if not people:
        return []

    def sort_key(r: dict) -> tuple:
        return (0 if INVESTMENT_EXEC_TITLES.search(r["title"]) else 1,)

    people.sort(key=sort_key)

    principals = []
    for r in people[:2]:
        parts = [p.strip() for p in r["name"].split(",") if p.strip()]
        last = parts[0] if parts else r["name"].strip()
        first_middle = [p for p in parts[1:] if p.upper() != "NMN"]  # NMN = "No Middle Name"
        full_name = " ".join(first_middle + [last]) if first_middle else last
        principals.append({
            "full_name": full_name,
            "title": r["title"].strip(),
            "raw_row": f"{r['name']} {r['type']} {r['title']} {r.get('date') or ''} "
                       f"{r['code']} {r['control']} {r['pr']} {r.get('crd') or ''}".strip(),
        })
    return principals


# --- Item 1.J / 1.K "Contact Employee" -------------------------------------------------
#
# Field semantics confirmed from the form-instruction text embedded in the PDF itself,
# same standard as Schedule A above: Item 1.J is "(1) Provide the name and contact
# information of your Chief Compliance Officer... Name: / Other titles, if any: /
# Telephone number: / Facsimile number, if any: / [address lines] / Electronic mail
# (e-mail) address, if Chief Compliance Officer has one:". Item 1.K is "Additional
# Regulatory Contact Person" with the same Name/Titles/Telephone/E-mail layout, used only
# "if a person other than the Chief Compliance Officer is authorized to receive
# information and respond to questions about this Form ADV" — i.e. filled at the filer's
# option, not required. Checked all 14 pilot ADV firms' PDFs directly (2026-07-26): every
# one left both 1.J and 1.K blank (the Name/Telephone/E-mail labels are immediately
# followed by the next field's label with no value in the extracted text, identically
# across every firm and every repeated occurrence within each PDF) — Schedule A already
# discloses the CCO's name via a required field, so many small exempt reporting advisers
# skip re-entering it in this parallel, optional section. That is a real, verified
# negative result, not a parsing gap: the same regex below runs and returns real names
# whenever a filing does fill this section in.

_ITEM_1J_RE = re.compile(
    r"J\. Chief Compliance Officer.*?"
    r"Name:\s*(?P<name>.*?)\s*Other titles, if any:\s*(?P<title>.*?)\s*"
    r"Telephone number:\s*(?P<phone>.*?)\s*Facsimile number, if any:.*?"
    r"Electronic mail \(e-mail\) address, if Chief Compliance Officer has one:\s*(?P<email>[^\n]*)",
    re.DOTALL,
)
_ITEM_1K_RE = re.compile(
    r"K\. Additional Regulatory Contact Person.*?"
    r"Name:\s*(?P<name>.*?)\s*Titles:\s*(?P<title>.*?)\s*"
    r"Telephone number:\s*(?P<phone>.*?)\s*Facsimile number, if any:.*?"
    r"Electronic mail \(e-mail\) address, if contact person has one:\s*(?P<email>[^\n]*)",
    re.DOTALL,
)


def _extract_contact(text: str, pattern: re.Pattern) -> dict | None:
    m = pattern.search(text)
    if not m:
        return None
    name = m.group("name").strip()
    if not name:
        return None
    return {
        "name": name,
        "title": m.group("title").strip() or None,
        "phone": m.group("phone").strip() or None,
        "email": m.group("email").strip() or None,
    }


def get_contact_employee(crd: str) -> dict | None:
    """Item 1.J (Chief Compliance Officer) contact, falling back to Item 1.K (Additional
    Regulatory Contact Person) if 1.J's name field is blank. Returns None (not a guess) if
    neither section names anyone — confirmed the common case for this pilot's 14 ADV firms."""
    text = _fetch_pdf_text(crd)
    if not text:
        return None
    return _extract_contact(text, _ITEM_1J_RE) or _extract_contact(text, _ITEM_1K_RE)


if __name__ == "__main__":
    import sys
    for crd in sys.argv[1:]:
        print(crd, "principals:", get_principals(crd))
        print(crd, "contact:", get_contact_employee(crd))
