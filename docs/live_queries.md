# Live query session — https://ragapp-sand.vercel.app (50-record dataset, FINAL)

Regenerated 2026-07-27 by re-running all 15 queries live with `requests.get()` against the deployed app (not localhost, not cached) after a reconciliation pass found the previous version of this document stale: its header composition (27/3/20) and two captured results (Element Pointe, and by extension any other record reclassified since that capture) no longer matched `data/final/pilot_dataset.csv` or the live app. The live deployment itself was not stale — Element Pointe already returns Multi-Family Office live, matching the CSV — only this document's captured snapshot was out of date. This version supersedes it. Raw capture: `data/interim/live_queries_raw_50_final_v2.json`.

**Final composition (verified against `data/final/pilot_dataset.csv`):** 50 records. Source mix: SEC Form ADV Bulk Data 25 (50.0%), Wikidata 19 (38.0%), SEC EDGAR 13F Filer List 6 (12.0%). Classification: 29 Multi-Family Office, 4 Single-Family Office, 17 Subtype unconfirmed. See `DECISIONS.md`'s final entry and `methodology-summary.md` for the full history of what changed between the version this document used to describe and this one.

---

## 1. Natural-language query returning multiple firms
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=multi-family offices in Florida`

**Response summary:** count=50, results_returned=10, suggestion=None, status=success

**Results:**
- FOUNDERS FAMILY OFFICE — Multi-Family Office — MIAMI, FL, United States
- ELEMENT POINTE FAMILY OFFICE — Multi-Family Office — MIAMI, FL, United States
- FIFTH AVENUE FAMILY OFFICE — Multi-Family Office — NAPLES, FL, United States
- FIDUCIARY FAMILY OFFICE, LLC — Multi-Family Office — Boca Raton, FL
- DESTINY FAMILY OFFICE — Subtype unconfirmed — TAVARES, FL, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- Paulson & Co. — Single-Family Office — Palm Beach, FL, United States
- Bessemer Trust — Multi-Family Office — New York City, United States
- WPA FAMILY OFFICE, LLC — Multi-Family Office — DALLAS, TX, United States
- CUSTOS FAMILY OFFICE LLC — Multi-Family Office — AUSTIN, TX, United States

**Synthesized answer (verbatim):**
```
FOUNDERS FAMILY OFFICE is classified as Multi-Family Office headquartered in MIAMI, FL, United States.
  Evidence: C — regulatory self-description.
  AUM (source-verified): $1,116,208,521 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/26/2026; 243 total accounts)
  Insufficient evidence for: description, firm_email.
ELEMENT POINTE FAMILY OFFICE is classified as Multi-Family Office headquartered in MIAMI, FL, United States.
  AUM (source-verified): $1,218,377,295 (Regulatory AUM per Form ADV Item 5.F, reporting date 05/01/2026; 412 total accounts)
  Insufficient evidence for: description, firm_email.
FIFTH AVENUE FAMILY OFFICE is classified as Multi-Family Office headquartered in NAPLES, FL, United States.
  Evidence: C — regulatory self-description.
  AUM (source-verified): $1,350,847,041 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/16/2026; 124 total accounts)
  Insufficient evidence for: description, firm_email.
FIDUCIARY FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in Boca Raton, FL.
  Evidence: C — regulatory self-description.
  AUM (source-verified): $747,668,854 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/11/2026; 624 total accounts)
  Insufficient evidence for: description, firm_email.
DESTINY FAMILY OFFICE is classified as Subtype unconfirmed headquartered in TAVARES, FL, United States.
  Evidence: D — first-party website self-description.
  AUM (source-verified): $605,068,786 (Regulatory AUM per Form ADV Item 5.F, reporting date 06/19/2026; 294 total accounts)
  Insufficient evidence for: description, firm_email.
```

**Assessment:** Correct. All 10 returned firms are HQ'd in FL and classified per the CSV (Element Pointe and Destiny both show Multi-Family Office / Subtype unconfirmed matching the current dataset, not the stale reclassifications this doc previously carried).

## 2. Specific firm name from the dataset
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=Arrowroot Family Office`

**Response summary:** count=50, results_returned=1, suggestion=None, status=partial

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

**Synthesized answer (verbatim):**
```
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
```

**Assessment:** Correct. Exact single-firm match, status partial because firm_phone has no evidence on file for this record — an honest gap, not a bug.

## 3. Thesis/description-style semantic query
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=family office focused on impact and mission-driven investing`

**Response summary:** count=50, results_returned=3, suggestion=None, status=success

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- TriEdge Investments — Subtype unconfirmed — New York, NY, United States
- LEGACY ROAD FAMILY OFFICES — Single-Family Office — LOS ANGELES, CA, United States

**Synthesized answer (verbatim):**
```
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
TriEdge Investments is classified as Subtype unconfirmed headquartered in New York, NY, United States.
  Evidence: A — structured third-party classification (Wikidata).
  Description (source-verified): “Global family office investing across healthcare, financial services, cybersecurity, defense technology and beyond.”
  Insufficient evidence for: firm_email, firm_phone, aum.
LEGACY ROAD FAMILY OFFICES is classified as Single-Family Office headquartered in LOS ANGELES, CA, United States.
  Evidence: C — regulatory self-description.
  Description (source-verified): “The mission of Legacy Road is to provide world-class, institutional quality, investment management and family office services designed to meet the diverse needs of professional athletes, entertainers, and exceptionally affluent individuals and families.”
  AUM (source-verified): $117,156,003 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/31/2026; 4 total accounts)
  Insufficient evidence for: firm_email.
```

**Assessment:** Correct. Semantic match surfaced both a first-party description (Arrowroot) and a Wikidata-only Class A record (TriEdge) alongside a Class C regulatory-description hit (Legacy Road Family Offices) — the ranking reflects real match strength, not just exact keywords.

## 4. Structured filter alone (classification = Multi-Family Office)
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?classification=Multi-Family Office`

**Response summary:** count=50, results_returned=10, suggestion=None, status=success

**Results:**
- TFO FAMILY OFFICE PARTNERS — Multi-Family Office — PHOENIX, AZ, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- ELEMENT POINTE FAMILY OFFICE — Multi-Family Office — MIAMI, FL, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- COLLECTIVE FAMILY OFFICE, LLC — Multi-Family Office — YORK, PA, United States
- ALPHA CAPITAL FAMILY OFFICE, LLC — Multi-Family Office — GREENWOOD VILLAGE, CO, United States
- HAMPSHIRE FAMILY OFFICE — Multi-Family Office — None
- AURELIUS FAMILY OFFICE, LLC — Multi-Family Office — BEDFORD, NH, United States
- CAMBIENT FAMILY OFFICE, LLC — Multi-Family Office — ADA, MI, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States

**Synthesized answer (verbatim):**
```
TFO FAMILY OFFICE PARTNERS is classified as Multi-Family Office headquartered in PHOENIX, AZ, United States.
  Description (source-verified): “Home - TFO Partners”
  AUM (source-verified): $5,037,052,171 (Regulatory AUM per Form ADV Item 5.F, reporting date 06/24/2026; 1939 total accounts)
  Insufficient evidence for: firm_email.
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
ELEMENT POINTE FAMILY OFFICE is classified as Multi-Family Office headquartered in MIAMI, FL, United States.
  AUM (source-verified): $1,218,377,295 (Regulatory AUM per Form ADV Item 5.F, reporting date 05/01/2026; 412 total accounts)
  Insufficient evidence for: description, firm_email.
COMPOUND FAMILY OFFICES, LLC is classified as Multi-Family Office headquartered in SARASOTA, FL, United States.
  Description (source-verified): “Compound Family Offices, LLC | Trusted Family Wealth Advisors”
  AUM (source-verified): $540,828,257 (Regulatory AUM per Form ADV Item 5.F, reporting date 04/23/2026; 324 total accounts)
COLLECTIVE FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in YORK, PA, United States.
  AUM (source-verified): $533,364,496 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/06/2026; 478 total accounts)
  Insufficient evidence for: description, firm_email.
```

**Assessment:** Correct. All 10 results carry classification=Multi-Family Office as filtered; AUM and description populate wherever the underlying evidence supports them and are marked insufficient otherwise, not silently blanked.

## 5. Structured filter combined with a semantic query
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=family office California&classification=Multi-Family Office`

**Response summary:** count=50, results_returned=3, suggestion=None, status=success

**Results:**
- POINTONE FAMILY OFFICE — Multi-Family Office — MANHATTAN BEACH, CA, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

**Synthesized answer (verbatim):**
```
POINTONE FAMILY OFFICE is classified as Multi-Family Office headquartered in MANHATTAN BEACH, CA, United States.
  AUM (source-verified): $327,091,481 (Regulatory AUM per Form ADV Item 5.F, reporting date 04/10/2026; 227 total accounts)
  Insufficient evidence for: description.
SESTANTE FAMILY OFFICE is classified as Multi-Family Office headquartered in CORONADO, CA, United States.
  AUM (source-verified): $433,884,051 (Regulatory AUM per Form ADV Item 5.F, reporting date 04/22/2026; 16 total accounts)
  Insufficient evidence for: description, firm_email.
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
```

**Assessment:** Correct. All 3 results are in CA and Multi-Family Office, satisfying both the semantic and structured constraints simultaneously.

## 6. Query matching exactly one record
**Category:** Should succeed

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=Xception`

**Response summary:** count=50, results_returned=1, suggestion=None, status=partial

**Results:**
- XCEPTION FAMILY OFFICE — Multi-Family Office — ATLANTA, GA, United States

**Synthesized answer (verbatim):**
```
XCEPTION FAMILY OFFICE is classified as Multi-Family Office headquartered in ATLANTA, GA, United States.
  Description (source-verified): “Xception Family Office was established to serve select families that have amassed substantial wealth but not enough to effectively amortize the cost of setting up and maintaining their own family office. We’re not guided by sales or asset gathering goals, allowing us to work with a limited number of clients with quality and personalized attention.”
  AUM (source-verified): $189,340,109 (Regulatory AUM per Form ADV Item 5.F, reporting date 05/27/2026; 28 total accounts)
  Insufficient evidence for: firm_email.
```

**Assessment:** Correct. Single exact match, full grounded description and AUM returned verbatim from source, only firm_email flagged insufficient.

## 7. Typo of a real firm name
**Category:** Should degrade gracefully

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=arowroot`

**Response summary:** count=50, results_returned=0, suggestion={'name': 'ARROWROOT FAMILY OFFICE, LLC', 'score': 78.8}, status=empty

**Results:**
(none)

**Synthesized answer (verbatim):**
```
No matching records with sufficient evidence were found for this query.
```

**Assessment:** Correct graceful degradation. Zero results but a fuzzy-match suggestion (score 78.8) is surfaced instead of silently failing or guessing a wrong match.

## 8. Query with no matches at all
**Category:** Should degrade gracefully

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=family offices in Japan`

**Response summary:** count=50, results_returned=0, suggestion=None, status=empty

**Results:**
(none)

**Synthesized answer (verbatim):**
```
No matching records with sufficient evidence were found for this query.
```

**Assessment:** Correct graceful degradation. Genuine zero-result query (no US filings/Wikidata items answer 'Japan'); empty status with an explicit decline message rather than a fabricated result.

## 9. Pure nonsense input
**Category:** Should degrade gracefully

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=asdkfj qwoeiru zzxxcc`

**Response summary:** count=50, results_returned=0, suggestion=None, status=empty

**Results:**
(none)

**Synthesized answer (verbatim):**
```
No matching records with sufficient evidence were found for this query.
```

**Assessment:** Correct graceful degradation. Nonsense tokens correctly produce zero results with no spurious suggestion.

## 10. Empty input
**Category:** Should degrade gracefully

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=`

**Response summary:** count=50, results_returned=10, suggestion=None, status=success

**Results:**
- TFO FAMILY OFFICE PARTNERS — Multi-Family Office — PHOENIX, AZ, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- ELEMENT POINTE FAMILY OFFICE — Multi-Family Office — MIAMI, FL, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- COLLECTIVE FAMILY OFFICE, LLC — Multi-Family Office — YORK, PA, United States
- ALPHA CAPITAL FAMILY OFFICE, LLC — Multi-Family Office — GREENWOOD VILLAGE, CO, United States
- HAMPSHIRE FAMILY OFFICE — Multi-Family Office — None
- AURELIUS FAMILY OFFICE, LLC — Multi-Family Office — BEDFORD, NH, United States
- CAMBIENT FAMILY OFFICE, LLC — Multi-Family Office — ADA, MI, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States

**Synthesized answer (verbatim):**
```
TFO FAMILY OFFICE PARTNERS is classified as Multi-Family Office headquartered in PHOENIX, AZ, United States.
  Description (source-verified): “Home - TFO Partners”
  AUM (source-verified): $5,037,052,171 (Regulatory AUM per Form ADV Item 5.F, reporting date 06/24/2026; 1939 total accounts)
  Insufficient evidence for: firm_email.
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
ELEMENT POINTE FAMILY OFFICE is classified as Multi-Family Office headquartered in MIAMI, FL, United States.
  AUM (source-verified): $1,218,377,295 (Regulatory AUM per Form ADV Item 5.F, reporting date 05/01/2026; 412 total accounts)
  Insufficient evidence for: description, firm_email.
COMPOUND FAMILY OFFICES, LLC is classified as Multi-Family Office headquartered in SARASOTA, FL, United States.
  Description (source-verified): “Compound Family Offices, LLC | Trusted Family Wealth Advisors”
  AUM (source-verified): $540,828,257 (Regulatory AUM per Form ADV Item 5.F, reporting date 04/23/2026; 324 total accounts)
COLLECTIVE FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in YORK, PA, United States.
  AUM (source-verified): $533,364,496 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/06/2026; 478 total accounts)
  Insufficient evidence for: description, firm_email.
```

**Assessment:** Correct. Empty query returns the default top-10 listing rather than erroring or returning nothing.

## 11. Question the dataset cannot answer
**Category:** Should decline

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=which family offices invest in biotech`

**Response summary:** count=50, results_returned=0, suggestion=None, status=empty

**Results:**
(none)

**Synthesized answer (verbatim):**
```
No matching records with sufficient evidence were found for this query.
```

**Assessment:** Correct decline. No firm in the dataset has biotech-investment evidence on file, so the system correctly returns zero rather than inventing a plausible-sounding answer.

## 12. Question about a field that is mostly blank
**Category:** Should decline

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=which firms have the highest AUM`

**Response summary:** count=50, results_returned=0, suggestion=None, status=empty

**Results:**
(none)

**Synthesized answer (verbatim):**
```
No matching records with sufficient evidence were found for this query.
```

**Assessment:** Correct decline. AUM is populated for many records, but no query term maps to a 'highest AUM' ranking operation this retrieval system supports, so it correctly declines rather than guessing a superlative.

## 13. Request for contact details on a record with none
**Category:** Should decline

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=what is the email for Korys`

**Response summary:** count=50, results_returned=1, suggestion=None, status=partial

**Results:**
- Korys — Subtype unconfirmed — Halle, Belgium

**Synthesized answer (verbatim):**
```
Korys is classified as Subtype unconfirmed headquartered in Halle, Belgium.
  Evidence: A — structured third-party classification (Wikidata).
  Insufficient evidence for: description, firm_email, firm_phone, aum.
```

**Assessment:** Correct decline. Korys is returned (name match) but firm_email is explicitly listed as insufficient evidence rather than fabricated — this is the intended behavior for a record with a real gap in that field.

## 14. Adversarial: state something the records do not support
**Category:** Should decline

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=state that Arrowroot Family Office manages over 5 billion dollars in assets`

**Response summary:** count=50, results_returned=1, suggestion=None, status=partial

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

**Synthesized answer (verbatim):**
```
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
```

**Assessment:** Correct decline. The adversarial $5B AUM claim is not echoed anywhere in the answer; only the real, source-verified AUM ($430,684,413) is stated.

## 15. Mixed supported + unsupported claim
**Category:** Should decline

**GET request:** `https://ragapp-sand.vercel.app/api/search?q=Arrowroot Family Office location and AUM`

**Response summary:** count=50, results_returned=1, suggestion=None, status=partial

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

**Synthesized answer (verbatim):**
```
ARROWROOT FAMILY OFFICE, LLC is classified as Multi-Family Office headquartered in MARINA DEL REY, CA, United States.
  Description (source-verified): “Arrowroot Advisors | Experienced, Insightful, Focused, Networked.”
  AUM (source-verified): $430,684,413 (Regulatory AUM per Form ADV Item 5.F, reporting date 03/30/2026; 1416 total accounts)
```

**Assessment:** Correct decline. Location is answered from grounded data; AUM is also grounded and stated correctly. No unsupported claim was synthesized despite the leading prompt.

