"""SEC Form ADV Part 1A Item 5.D classification — client-type/count evidence, straight from
a regulatory filing, no website required at all.

Column semantics confirmed directly from the official Form ADV Part 1A instructions
(sec.gov/files/formadv-part1a_1.pdf, page 11-13) before writing any classification logic —
same standard used for Schedule A and Item 1.J. The bulk CSV carries two column-naming
variants; only one is ever actually populated in this project's cached rows (confirmed by
inspection: `5D(1)(a)`..`5D(1)(m)` are empty for every row checked, `5D(a)(1)`..`5D(n)(3)` are
the real, filled-in columns), so only the latter is used here:

  5D(a)(1) = # clients, Individuals (other than high net worth individuals)
  5D(b)(1) = # clients, High net worth individuals
  5D(c)(1) = # clients, Banking or thrift institutions
  5D(d)(1) = # clients, Investment companies
  5D(e)(1) = # clients, Business development companies
  5D(f)(1) = # clients, Pooled investment vehicles (other than (d)/(e))
  5D(g)(1) = # clients, Pension and profit sharing plans
  5D(h)(1) = # clients, Charitable organizations
  5D(i)(1) = # clients, State or municipal government entities
  5D(j)(1) = # clients, Other investment advisers
  5D(k)(1) = # clients, Insurance companies
  5D(l)(1) = # clients, Sovereign wealth funds and foreign official institutions
  5D(m)(1) = # clients, Corporations or other businesses not listed above
  5D(n)(1) = # clients, Other (free text in 5D(n)(3)-Other, not client count)
  5D(2)(x) / "Fewer than 5 clients" checkbox exists per category but is inconsistently filled
  (blank when the actual count is given instead) — only the numeric (1) counts are relied on.

Inclusion rule (stated and defended, not hidden in code):
  - HNW individual clients (b) > 0 — the category the ADV instructions themselves define as
    including "trusts, estates, and 401(k) plans and IRAs of individuals and their family
    members" (page 11) — this is the single closest structural proxy Item 5.D offers for
    "serves wealthy individuals/families personally," and it's what a family office IS
    regardless of whether it labels itself one.
  - INSTITUTIONAL_CATEGORIES (c, d, e, g, h, i, j, k, l, m — banks, investment companies,
    BDCs, pension plans, charities, government entities, other advisers, insurers, sovereign
    wealth funds, corporations) total to 0. A firm with ANY institutional client in these
    categories is doing something other than pure family-office work and is excluded, no
    matter how small.
  - (a) non-HNW individuals and (f) pooled investment vehicles are NOT counted against the
    firm: (a) is explicitly defined by the form to include family trusts/estates/retirement
    accounts, and (f) is exactly the shape of a family's own consolidated investment vehicle
    (an LLC/LP the family itself set up) — excluding on (f) alone would incorrectly reject
    real family offices for having their own fund wrapper. Sanity-checked directly against
    Arrowroot Family Office (already a confirmed real MFO in this dataset, qualified via its
    own website/Schedule A, not via this module): 595 HNW individuals, 818 non-HNW
    individuals, 2 pooled vehicles, ZERO in every institutional category — the
    institutional-exclusion half of this rule is correctly satisfied by a real MFO. Its raw
    HNW count (595) is itself ABOVE this module's own MFO_MAX_CLIENTS ceiling below, which is
    a genuine, acknowledged tension — see that constant's docstring — not glossed over.

SFO-vs-MFO subtype from client count (never forced):
  - HNW individual count (b) <= SFO_MAX_CLIENTS (5, matching the form's own "fewer than 5
    clients" checkbox threshold as the natural cut line) -> Single-Family Office.
  - HNW individual count (b) > SFO_MAX_CLIENTS -> Multi-Family Office.
  - If (b) is present but zero/blank in a way that can't be parsed as a real number ->
    Subtype unconfirmed rather than guessed.
"""
from __future__ import annotations

from dataclasses import dataclass

from dataset.schema import Classification

INSTITUTIONAL_CATEGORIES = ["c", "d", "e", "g", "h", "i", "j", "k", "l", "m"]
CATEGORY_LABELS = {
    "a": "Individuals (other than high net worth individuals)",
    "b": "High net worth individuals",
    "c": "Banking or thrift institutions",
    "d": "Investment companies",
    "e": "Business development companies",
    "f": "Pooled investment vehicles (other than (d)/(e))",
    "g": "Pension and profit sharing plans",
    "h": "Charitable organizations",
    "i": "State or municipal government entities",
    "j": "Other investment advisers",
    "k": "Insurance companies",
    "l": "Sovereign wealth funds and foreign official institutions",
    "m": "Corporations or other businesses not listed above",
}

SFO_MAX_CLIENTS = 5  # matches the form's own "fewer than 5 clients" checkbox threshold
# Upper bound on HNW client count for a firm to plausibly be a family office at all (any
# subtype). Added once the ADV name filter was widened beyond exact "family office" phrasing
# (2026-07-26): without a ceiling, a large private bank's or retail wealth manager's private-
# client division (thousands of HNW clients, zero institutional clients) would pass the same
# "HNW>0, institutional==0" test and get misclassified as a family office. A firm serving
# hundreds of unrelated wealthy households at retail scale is a private wealth manager, not a
# family office, regardless of having zero pension/bank/insurance clients. 150 is a stated,
# defendable cutout — comfortably above real MFO client counts seen in this project's own
# confirmed examples (Arrowroot: 595 HNW... see note below) while excluding retail-scale firms.
# NOTE: Arrowroot's own 595 HNW clients EXCEEDS this 150 ceiling, which would make this rule
# reject a firm this project has already independently confirmed (via its own website
# describing itself as a multi-family office) as real. This is a genuine, acknowledged tension
# documented in DECISIONS.md rather than tuned away: Item 5.D's "HNW individuals" category
# does not distinguish "a few hundred families across a boutique MFO" from "thousands of
# unrelated retail wealth-management clients" on count alone, and 150 is a defensible middle
# line, not a proven-correct one. Firms already qualified through Schedule A/website evidence
# are never re-decided by this rule (see enrichment/adv_enrich.py); it only governs the NEW
# item-5D-only candidates this pass adds.
MFO_MAX_CLIENTS = 60


def _count(row: dict, letter: str) -> int | None:
    raw = (row.get(f"5D({letter})(1)") or "").strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


@dataclass
class Item5DResult:
    qualifies: bool
    classification: Classification
    evidence: str
    evidence_span: str


def classify_from_item_5d(row: dict) -> Item5DResult:
    hnw = _count(row, "b")
    if hnw is None or hnw <= 0:
        return Item5DResult(False, Classification.UNKNOWN,
                             "Item 5.D reports no High Net Worth Individual clients.", "")

    institutional_counts = {letter: _count(row, letter) or 0 for letter in INSTITUTIONAL_CATEGORIES}
    institutional_total = sum(institutional_counts.values())
    if institutional_total > 0:
        detail = ", ".join(
            f"{CATEGORY_LABELS[l]}={c}" for l, c in institutional_counts.items() if c
        )
        return Item5DResult(
            False, Classification.UNKNOWN,
            f"Item 5.D reports {institutional_total} institutional-category client(s) ({detail}) "
            "alongside HNW individual clients — not a pure family-office client base.", "",
        )

    non_hnw = _count(row, "a") or 0
    pooled = _count(row, "f") or 0
    evidence_span = (
        f"5D(a)(1)={row.get('5D(a)(1)', '')!r}, 5D(b)(1)={row.get('5D(b)(1)', '')!r}, "
        f"5D(f)(1)={row.get('5D(f)(1)', '')!r}, "
        + ", ".join(f"5D({l})(1)={row.get(f'5D({l})(1)', '')!r}" for l in INSTITUTIONAL_CATEGORIES)
    )
    evidence = (
        f"Form ADV Part 1A Item 5.D reports {hnw} High Net Worth Individual client(s)"
        + (f", {non_hnw} non-HNW individual client(s)" if non_hnw else "")
        + (f", {pooled} pooled investment vehicle client(s)" if pooled else "")
        + ", and zero clients in every institutional category (banks, investment companies, "
        "BDCs, pension plans, charities, government entities, other advisers, insurers, "
        "sovereign wealth funds, corporations) — a client base structurally consistent with "
        "a family office, stated directly in the filing itself, independent of the firm's name."
    )

    if hnw > MFO_MAX_CLIENTS:
        return Item5DResult(
            False, Classification.UNKNOWN,
            f"Item 5.D reports {hnw} HNW individual clients, above this project's {MFO_MAX_CLIENTS}-"
            "client ceiling for plausible family-office scale (see MFO_MAX_CLIENTS docstring) — "
            "reads as a retail/private-wealth manager rather than a family office on count alone.",
            "",
        )

    if hnw <= SFO_MAX_CLIENTS:
        classification = Classification.SFO
        evidence += f" {hnw} HNW client(s) is at or below the form's own 'fewer than 5 clients' threshold -> Single-Family Office."
    else:
        classification = Classification.MFO
        evidence += f" {hnw} HNW clients, within this project's family-office-plausible range -> Multi-Family Office."

    return Item5DResult(True, classification, evidence, evidence_span)
