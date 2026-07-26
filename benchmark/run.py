"""Benchmark the real pipeline against the hand-verified ground truth fixtures.

Per Correction 3: the 18 hand-researched records are an evaluation set, not a
data source. This script runs discovery + enrichment fresh and reports:
  1. Discovery recall — of the ground-truth firms, how many does the
     pipeline's discovery layer surface as a candidate at all?
  2. Field-level agreement — for firms the pipeline actually enriched, does
     its value for each field match / miss / contradict the hand-verified one?
  3. Contradictions, listed individually, not summarized away — each one is
     either a pipeline bug or an error in the original hand research.

Run with: python -m benchmark.run
"""
from __future__ import annotations

from rapidfuzz import fuzz

from dataset.schema import Firm
from discovery.store import load_candidates
from enrichment.pipeline import run_enrichment
from tests.fixtures.hand_verified_ground_truth_1 import PILOT_FIRMS
from tests.fixtures.hand_verified_ground_truth_2 import BATCH2_FIRMS
from tests.fixtures.hand_verified_ground_truth_3 import BATCH3_FIRMS

GROUND_TRUTH: list[Firm] = PILOT_FIRMS + BATCH2_FIRMS + BATCH3_FIRMS

COMPARE_FIELDS = ["hq_city", "hq_state", "firm_phone"]  # fields the current deterministic
# enrichers can plausibly populate; description/thesis/sectors/aum need the LLM extraction
# path, which requires ANTHROPIC_API_KEY (not set in this environment) — see DECISIONS.md.

NAME_MATCH_THRESHOLD = 82  # rapidfuzz token_sort_ratio


import re

US_STATE_ABBREV = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar", "california": "ca",
    "colorado": "co", "connecticut": "ct", "delaware": "de", "florida": "fl", "georgia": "ga",
    "hawaii": "hi", "idaho": "id", "illinois": "il", "indiana": "in", "iowa": "ia",
    "kansas": "ks", "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri", "south carolina": "sc",
    "south dakota": "sd", "tennessee": "tn", "texas": "tx", "utah": "ut", "vermont": "vt",
    "virginia": "va", "washington": "wa", "west virginia": "wv", "wisconsin": "wi",
    "wyoming": "wy",
}


def _norm(name: str) -> str:
    return name.lower().replace(",", "").replace(".", "").strip()


def _values_equivalent(field: str, gt_val, pf_val) -> bool:
    """Field-aware equivalence so formatting differences (full state name vs
    abbreviation, E.164 vs raw-digit phone) don't get reported as
    contradictions — those aren't disagreements, they're normalization gaps."""
    a, b = _norm(str(gt_val or "")), _norm(str(pf_val or ""))
    if a == b:
        return True
    if field == "hq_state":
        a = US_STATE_ABBREV.get(a, a)
        b = US_STATE_ABBREV.get(b, b)
        return a == b
    if field == "firm_phone":
        digits_a = re.sub(r"\D", "", str(gt_val or ""))
        digits_b = re.sub(r"\D", "", str(pf_val or ""))
        # compare last 10 digits so a leading US country code doesn't cause a false mismatch
        return bool(digits_a) and bool(digits_b) and digits_a[-10:] == digits_b[-10:]
    return False


def discovery_recall(ground_truth: list[Firm]) -> tuple[list[Firm], list[Firm]]:
    candidates = load_candidates()
    candidate_names = [_norm(c.name_as_found) for c in candidates]
    found, missed = [], []
    for gt in ground_truth:
        gt_name = _norm(gt.name.split(" (")[0])  # strip "(Elon Musk Family Office)"-style annotations
        hit = any(fuzz.token_sort_ratio(gt_name, cn) >= NAME_MATCH_THRESHOLD for cn in candidate_names)
        (found if hit else missed).append(gt)
    return found, missed


def _match_pipeline_firm(gt: Firm, pipeline_firms: list[Firm]) -> Firm | None:
    gt_name = _norm(gt.name.split(" (")[0])
    best, best_score = None, 0
    for pf in pipeline_firms:
        score = fuzz.token_sort_ratio(gt_name, _norm(pf.name))
        if score > best_score:
            best, best_score = pf, score
    return best if best_score >= NAME_MATCH_THRESHOLD else None


def field_agreement(ground_truth: list[Firm], pipeline_firms: list[Firm]) -> dict:
    report = {f: {"match": 0, "miss": 0, "contradiction": 0} for f in COMPARE_FIELDS}
    contradictions = []
    matched_pairs = []

    for gt in ground_truth:
        pf = _match_pipeline_firm(gt, pipeline_firms)
        if pf is None:
            continue
        matched_pairs.append((gt, pf))
        for field in COMPARE_FIELDS:
            gt_val = _field_value(gt, field)
            pf_val = _field_value(pf, field)
            if pf_val is None:
                report[field]["miss"] += 1
            elif _values_equivalent(field, gt_val, pf_val):
                report[field]["match"] += 1
            else:
                report[field]["contradiction"] += 1
                contradictions.append({
                    "firm": gt.name, "field": field,
                    "ground_truth": gt_val, "pipeline": pf_val,
                })
    return {"report": report, "contradictions": contradictions, "matched_pairs": matched_pairs}


def _field_value(firm: Firm, field: str):
    if field == "firm_phone":
        return firm.firm_phone.value
    return getattr(firm, field, None)


def main() -> None:
    pipeline_firms, skipped, entity_rejected = run_enrichment()

    found, missed = discovery_recall(GROUND_TRUTH)
    print(f"=== Discovery recall: {len(found)}/{len(GROUND_TRUTH)} ground-truth firms "
          f"surfaced as a candidate by discovery/edgar.py + discovery/propublica.py ===")
    print(f"(Only 2 of ~9 planned discovery channels exist as code right now — the other 7 "
          f"channels named in the brief are still hand-research-only, so most misses below are "
          f"expected, not pipeline bugs.)")
    for f in missed:
        print(f"  MISSED: {f.name}  (discovery_source in ground truth: {f.discovery_source})")

    agreement = field_agreement(GROUND_TRUTH, pipeline_firms)
    print(f"\n=== Field-level agreement, {len(agreement['matched_pairs'])} firm(s) matched "
          f"between ground truth and pipeline output ===")
    for field, counts in agreement["report"].items():
        print(f"  {field}: match={counts['match']} miss={counts['miss']} "
              f"contradiction={counts['contradiction']}")

    print(f"\n=== Contradictions ({len(agreement['contradictions'])}), listed individually ===")
    if not agreement["contradictions"]:
        print("  none")
    for c in agreement["contradictions"]:
        print(f"  {c['firm']} / {c['field']}: ground_truth={c['ground_truth']!r} "
              f"vs pipeline={c['pipeline']!r}")

    print(f"\n{len(pipeline_firms)} firm(s) enriched by the pipeline this run "
          f"({len(skipped)} candidate(s) skipped — no enricher for their source yet).")


if __name__ == "__main__":
    main()
