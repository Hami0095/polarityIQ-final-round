"""One-off patch: fill principal_1/2 (CEO/founder), hq_country, and a founding-date signal
for the 14 Wikidata-sourced rows in data/final/pilot_dataset.csv, from
enrichment/wikidata_details_enrich.py's SPARQL results. Never overwrites a value already
present (regulatory-sourced or otherwise) — only fills currently-blank cells.
"""
import csv
import json
from pathlib import Path

FINAL = Path("data/final/pilot_dataset.csv")
DETAILS = json.loads(Path("data/interim/wikidata_details.json").read_text(encoding="utf-8"))
ROWS_CACHE = json.loads(Path("data/interim/wikidata_rows.json").read_text(encoding="utf-8"))

# firm_id (as assembled) -> QID, via the same name-slug rule assemble.py's enrichers use
NAME_TO_QID = {v["name"].strip(): k for k, v in ROWS_CACHE.items()}


def slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


SLUG_TO_QID = {slug(name): qid for name, qid in NAME_TO_QID.items()}

rows = list(csv.DictReader(FINAL.open(encoding="utf-8")))
fieldnames = list(rows[0].keys())

patched = 0
for r in rows:
    if r["discovery_source"] != "Wikidata":
        continue
    qid = SLUG_TO_QID.get(r["firm_id"])
    if not qid:
        continue
    d = DETAILS.get(qid)
    if not d:
        continue
    item_uri = f"http://www.wikidata.org/entity/{qid}"

    principals = []
    if d["ceo"]:
        principals.append((d["ceo"], "Chief Executive Officer (Wikidata P169)"))
    for f in d["founders"]:
        if f == d["ceo"]:
            continue
        principals.append((f, "Founder (Wikidata P112)"))

    for i, (name, title) in enumerate(principals[:2], start=1):
        if not r[f"principal_{i}_name"].strip():
            r[f"principal_{i}_name"] = name
            r[f"principal_{i}_title"] = title

    if not r["hq_country"].strip() and d["country"]:
        r["hq_country"] = d["country"]
    if not r["hq_city"].strip() and d["hq"]:
        r["hq_city"] = d["hq"]

    if not r["signal_1"].strip() and d["inception"]:
        year = d["inception"][:4]
        r["signal_1"] = f"Firm founded {year} (Wikidata P571 inception claim)"
        r["signal_1_source"] = item_uri

    note = (
        " Second-pass Wikidata enrichment (2026-07-26): CEO/founder name+title (P169/P112) "
        "and founding-year signal (P571), where present, sourced to the Wikidata entity URL "
        "itself (structured claim, Evidence Class A) — not a Wikipedia article; this QID has "
        "no English Wikipedia sitelink at all (checked directly), so no article "
        "description/dated event was available. P2403 (total assets), P2139 (revenue), and "
        "P1128 (employees) were queried and confirmed absent for this item — left blank, not "
        "inferred."
    )
    if qid == "Q113288804":
        note += (
            " NOTE: this item's P169/P112 claims name Adam Neumann and Rebekah Neumann (the "
            "WeWork founders) as CEO/founders of a firm called '166 2nd Financial Services' — "
            "an unusual enough pairing on a small, obscure Wikidata item that it reads as "
            "plausible vandalism or a joke edit, not fact-checked against a second source in "
            "this pass. Flagged rather than silently trusted."
        )
    r["blind_spots"] = r["blind_spots"].rstrip() + note
    patched += 1

with FINAL.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Patched", patched, "Wikidata rows")
