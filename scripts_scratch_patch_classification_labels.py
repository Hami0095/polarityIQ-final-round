"""One-off patch: add `family_office_confirmed` and rewrite `classification` from
"Unable to Determine" to "Subtype unconfirmed" for confirmed-family-office records, per
the 2026-07-26 disambiguation fix. Surgical CSV edit (mirrors
scripts_scratch_patch_adv_principals.py) rather than a full pipeline re-run.
"""
import csv
from pathlib import Path

FINAL = Path("data/final/pilot_dataset.csv")

rows = list(csv.DictReader(FINAL.open(encoding="utf-8")))
fieldnames = list(rows[0].keys())
if "family_office_confirmed" not in fieldnames:
    idx = fieldnames.index("classification")
    fieldnames.insert(idx, "family_office_confirmed")

for r in rows:
    confirmed = bool(r.get("evidence_class", "").strip()) or r["classification"] not in (
        "Unable to Determine", "Subtype unconfirmed",
    )
    r["family_office_confirmed"] = "Yes" if confirmed else "No"
    if r["classification"] == "Unable to Determine" and r.get("evidence_class", "").strip():
        r["classification"] = "Subtype unconfirmed"

with FINAL.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Patched", len(rows), "rows")
