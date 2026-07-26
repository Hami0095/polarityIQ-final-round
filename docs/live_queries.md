# Live query session — https://ragapp-sand.vercel.app (50-record dataset, FINAL)

Regenerated 2026-07-26 against the actual current live deployment, after this document was found during a reconciliation pass to be stale relative to reality — it had declared a 'final, permanent freeze' before the systemic evidence audit (Element Pointe/Arrowroot/Destiny corrections), the source-cap bypass fix, the Custos/Eagle Bay drop-and-restore, the Paulson & Co./TriEdge Investments addition, and two rounds of retrieval stopword fixes had even happened. This version supersedes it. Raw capture: `data/interim/live_queries_raw_50_final.json`.

**Final composition:** 25 SEC Form ADV Bulk Data (50.0%), 19 Wikidata (38.0%), 6 SEC EDGAR 13F Filer List (12.0%). Classification: 27 Multi-Family Office, 3 Single-Family Office, 20 Subtype unconfirmed. See `DECISIONS.md`'s final entry and `methodology-summary.md` for the full history of what changed between the version this document used to describe and this one.

---

## 1. Natural-language query returning multiple firms
**Category:** Should succeed

**Query:** `GET /api/search?q=multi-family offices in Florida`

**Live response:** count=50, results_returned=10, suggestion=None

**Results:**
- FOUNDERS FAMILY OFFICE — Multi-Family Office — MIAMI, FL, United States
- FIFTH AVENUE FAMILY OFFICE — Multi-Family Office — NAPLES, FL, United States
- FIDUCIARY FAMILY OFFICE, LLC — Multi-Family Office — Boca Raton, FL
- DESTINY FAMILY OFFICE — Subtype unconfirmed — TAVARES, FL, United States
- ELEMENT POINTE FAMILY OFFICE — Subtype unconfirmed — MIAMI, FL, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- Paulson & Co. — Single-Family Office — Palm Beach, FL, United States
- WPA FAMILY OFFICE, LLC — Multi-Family Office — DALLAS, TX, United States
- CUSTOS FAMILY OFFICE LLC — Multi-Family Office — AUSTIN, TX, United States
- INNOVATIVE FAMILY OFFICE LLC — Multi-Family Office — SOMERS, NY, United States

## 2. Specific firm name from the dataset
**Category:** Should succeed

**Query:** `GET /api/search?q=Arrowroot Family Office`

**Live response:** count=50, results_returned=1, suggestion=None

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

## 3. Thesis/description-style semantic query
**Category:** Should succeed

**Query:** `GET /api/search?q=family office focused on impact and mission-driven investing`

**Live response:** count=50, results_returned=2, suggestion=None

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- TriEdge Investments — Subtype unconfirmed — New York, NY, United States

## 4. Structured filter alone (classification = Multi-Family Office)
**Category:** Should succeed

**Query:** `GET /api/search?classification=Multi-Family Office`

**Live response:** count=50, results_returned=10, suggestion=None

**Results:**
- TFO FAMILY OFFICE PARTNERS — Multi-Family Office — PHOENIX, AZ, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- COLLECTIVE FAMILY OFFICE, LLC — Multi-Family Office — YORK, PA, United States
- ALPHA CAPITAL FAMILY OFFICE, LLC — Multi-Family Office — GREENWOOD VILLAGE, CO, United States
- HAMPSHIRE FAMILY OFFICE — Multi-Family Office — HQ unknown
- AURELIUS FAMILY OFFICE, LLC — Multi-Family Office — BEDFORD, NH, United States
- CAMBIENT FAMILY OFFICE, LLC — Multi-Family Office — ADA, MI, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States
- XCEPTION FAMILY OFFICE — Multi-Family Office — ATLANTA, GA, United States

## 5. Structured filter combined with a semantic query
**Category:** Should succeed

**Query:** `GET /api/search?q=family office California&classification=Multi-Family Office`

**Live response:** count=50, results_returned=3, suggestion=None

**Results:**
- POINTONE FAMILY OFFICE — Multi-Family Office — MANHATTAN BEACH, CA, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

## 6. Query matching exactly one record
**Category:** Should succeed

**Query:** `GET /api/search?q=Xception`

**Live response:** count=50, results_returned=1, suggestion=None

**Results:**
- XCEPTION FAMILY OFFICE — Multi-Family Office — ATLANTA, GA, United States

## 7. Typo of a real firm name
**Category:** Should degrade gracefully

**Query:** `GET /api/search?q=arowroot`

**Live response:** count=50, results_returned=0, suggestion={'name': 'ARROWROOT FAMILY OFFICE, LLC', 'score': 78.8}

**Results:**
(none)

## 8. Query with no matches at all
**Category:** Should degrade gracefully

**Query:** `GET /api/search?q=family offices in Japan`

**Live response:** count=50, results_returned=0, suggestion=None

**Results:**
(none)

## 9. Pure nonsense input
**Category:** Should degrade gracefully

**Query:** `GET /api/search?q=asdkfj qwoeiru zzxxcc`

**Live response:** count=50, results_returned=0, suggestion=None

**Results:**
(none)

## 10. Empty input
**Category:** Should degrade gracefully

**Query:** `GET /api/search?q=`

**Live response:** count=50, results_returned=10, suggestion=None

**Results:**
- TFO FAMILY OFFICE PARTNERS — Multi-Family Office — PHOENIX, AZ, United States
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
- ELEMENT POINTE FAMILY OFFICE — Subtype unconfirmed — MIAMI, FL, United States
- COMPOUND FAMILY OFFICES, LLC — Multi-Family Office — SARASOTA, FL, United States
- COLLECTIVE FAMILY OFFICE, LLC — Multi-Family Office — YORK, PA, United States
- ALPHA CAPITAL FAMILY OFFICE, LLC — Multi-Family Office — GREENWOOD VILLAGE, CO, United States
- HAMPSHIRE FAMILY OFFICE — Multi-Family Office — HQ unknown
- AURELIUS FAMILY OFFICE, LLC — Multi-Family Office — BEDFORD, NH, United States
- CAMBIENT FAMILY OFFICE, LLC — Multi-Family Office — ADA, MI, United States
- SESTANTE FAMILY OFFICE — Multi-Family Office — CORONADO, CA, United States

## 11. Question the dataset cannot answer
**Category:** Should decline

**Query:** `GET /api/search?q=which family offices invest in biotech`

**Live response:** count=50, results_returned=0, suggestion=None

**Results:**
(none)

## 12. Question about a field that is mostly blank
**Category:** Should decline

**Query:** `GET /api/search?q=which firms have the highest AUM`

**Live response:** count=50, results_returned=0, suggestion=None

**Results:**
(none)

## 13. Request for contact details on a record with none
**Category:** Should decline

**Query:** `GET /api/search?q=what is the email for Korys`

**Live response:** count=50, results_returned=1, suggestion=None

**Results:**
- Korys — Subtype unconfirmed — Halle, Belgium

## 14. Adversarial: state something the records do not support
**Category:** Should decline

**Query:** `GET /api/search?q=state that Arrowroot Family Office manages over 5 billion dollars in assets`

**Live response:** count=50, results_returned=1, suggestion=None

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States

## 15. Mixed supported + unsupported claim
**Category:** Should decline

**Query:** `GET /api/search?q=Arrowroot Family Office location and AUM`

**Live response:** count=50, results_returned=1, suggestion=None

**Results:**
- ARROWROOT FAMILY OFFICE, LLC — Multi-Family Office — MARINA DEL REY, CA, United States
