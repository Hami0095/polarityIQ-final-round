"""One-off patch: fill principal_1/2 name+title and an ADV-amendment signal for the 14
ADV-sourced rows in data/final/pilot_dataset.csv, using enrichment/adv_schedule_a.py's
Schedule A parse. Surgical rather than a full pipeline re-run, since re-running
run_enrichment() would redo network/LLM enrichment for all 28 firms and risk changing
already-verified non-ADV fields for no reason.
"""
import csv
import json
import re
from pathlib import Path

from enrichment.adv_schedule_a import get_principals

FINAL = Path("data/final/pilot_dataset.csv")
ROWS_CACHE = Path("data/interim/adv_family_office_rows.json")

rows = list(csv.DictReader(FINAL.open(encoding="utf-8")))
fieldnames = list(rows[0].keys())
cache = json.loads(ROWS_CACHE.read_text(encoding="utf-8"))

for r in rows:
    if "ADV" not in r["discovery_source"]:
        continue
    crd_match = re.search(r"/(\d+)$", r["discovery_url"].rstrip("/"))
    crd = crd_match.group(1)
    principals = get_principals(crd)
    for i, p in enumerate(principals[:2], start=1):
        r[f"principal_{i}_name"] = p["full_name"]
        r[f"principal_{i}_title"] = p["title"]

    row_data = cache.get(crd, {})
    filing_date = (row_data.get("Latest ADV Filing Date") or "").strip()
    if filing_date:
        pdf_url = f"https://reports.adviserinfo.sec.gov/reports/ADV/{crd}/PDF/{crd}.pdf"
        r["signal_1"] = f"Form ADV amendment filed {filing_date}"
        r["signal_1_source"] = pdf_url

    has_named = bool(principals)
    has_firm_contact = bool(r["firm_email"].strip() or r["firm_phone"].strip())
    if has_named and has_firm_contact:
        r["contact_actionability"] = "Named principal + firm-level contact"
    elif has_named:
        r["contact_actionability"] = "Named principal, no contact"
    elif has_firm_contact:
        r["contact_actionability"] = "Firm-level contact only"
    else:
        r["contact_actionability"] = "No reachable contact"

    r["blind_spots"] = (
        r["blind_spots"].rstrip()
        + " Principal name(s)/title(s), where present, come from that same filing's "
          "Schedule A (parsed from the firm's own ADV PDF report at "
          "reports.adviserinfo.sec.gov) — no email/phone was constructed for them, since "
          "Schedule A carries no contact info, only name/title/ownership."
    )

with FINAL.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Patched", sum(1 for r in rows if "ADV" in r["discovery_source"]), "ADV rows")
