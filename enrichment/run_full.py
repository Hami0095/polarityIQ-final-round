"""Resumable full-pipeline runner. Each candidate is processed and its result appended to
data/interim/pipeline_progress.jsonl IMMEDIATELY, one line per candidate, flushed after every
write. If this process is killed partway through (session teardown, timeout, whatever), re-running
it skips every candidate already present in that file and picks up where it left off, rather than
losing all progress and starting over — the first full run attempt (2026-07-25) was killed by
session teardown with zero output written, which is exactly the failure mode this exists to avoid.

Run with: python -m enrichment.run_full
"""
from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dataset.classification import classify
from dataset.entity_filter import check_entity_type
from dataset.schema import Firm
from discovery.store import load_candidates
from discovery.websearch import SearchBlocked, classify_from_search_snippets, enrich_candidate_via_search
from enrichment.adv_enrich import enrich_adv_candidate
from enrichment.edgar_13f_enrich import enrich_13f_candidate
from enrichment.edgar_enrich import enrich_edgar_candidate
from enrichment.propublica_enrich import enrich_propublica_candidate
from enrichment.sec_submissions import enrich_from_submissions, extract_cik
from enrichment.website_resolve import enrich_website_for_firm
from enrichment.wikidata_enrich import enrich_wikidata_candidate

PROGRESS_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "pipeline_progress.jsonl"

DETERMINISTIC_ENRICHERS = {
    "SEC EDGAR Form D": enrich_edgar_candidate,
    "ProPublica Nonprofit Explorer (990)": enrich_propublica_candidate,
    "SEC Form ADV Bulk Data": enrich_adv_candidate,
    "Wikidata": enrich_wikidata_candidate,
    "SEC EDGAR 13F Filer List": enrich_13f_candidate,
}


def _load_done_ids() -> set[str]:
    if not PROGRESS_PATH.exists():
        return set()
    done = set()
    with PROGRESS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                done.add(json.loads(line)["candidate_id"])
    return done


_append_lock = threading.Lock()


def _append(record: dict) -> None:
    # This is the resumability guarantee (append-and-skip-done-ids), so it must stay
    # correct under concurrency: one writer at a time, one JSON object per line, flushed
    # immediately — a torn/interleaved write here would corrupt the file every future run
    # reads to decide what's already done.
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _append_lock:
        with PROGRESS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
            f.flush()


def _classification_source_text(firm: Firm) -> str:
    parts = [firm.description.value, firm.investment_thesis.value, firm.blind_spots]
    return " ".join(p for p in parts if p)


def process_one(record, use_websearch_fallback: bool = True) -> dict:
    entity_check = check_entity_type(record.name_as_found)
    if entity_check.rejected:
        return {"candidate_id": record.candidate_id, "outcome": "entity_rejected",
                "name": record.name_as_found, "discovery_source": record.discovery_source,
                "reason": entity_check.reason, "evidence_span": entity_check.evidence_span}

    enricher = DETERMINISTIC_ENRICHERS.get(record.discovery_source)
    if enricher is None:
        return {"candidate_id": record.candidate_id, "outcome": "skipped",
                "name": record.name_as_found, "discovery_source": record.discovery_source,
                "reason": "no deterministic enricher for this source"}

    firm = enricher(record)
    if firm is None:
        return {"candidate_id": record.candidate_id, "outcome": "skipped",
                "name": record.name_as_found, "discovery_source": record.discovery_source,
                "reason": "deterministic enrichment returned nothing (unreachable/unparseable)"}

    if record.discovery_source in ("SEC EDGAR Form D", "SEC EDGAR 13F Filer List"):
        cik = extract_cik(record.notes)
        if cik:
            firm = enrich_from_submissions(firm, cik)

    firm = enrich_website_for_firm(firm)

    if not firm.website and use_websearch_fallback:
        # SearchBlocked is deliberately NOT caught here — it must propagate to main(), which
        # stops the whole run rather than let a rate-limited/blocked search engine masquerade
        # as "no operating entity found" for every remaining candidate (see SearchBlocked
        # docstring in discovery/websearch.py — this is exactly the failure mode that
        # happened on the first full-pipeline attempt, 2026-07-25).
        firm, resolved = enrich_candidate_via_search(firm)
        if not resolved and record.discovery_source == "SEC EDGAR Form D":
            return {"candidate_id": record.candidate_id, "outcome": "entity_rejected",
                    "name": firm.name, "discovery_source": firm.discovery_source,
                    "reason": "web search entity resolution found no operating site distinct "
                              "from the filing vehicle"}

    if firm.classification.value == "Unable to Determine":
        result = classify(_classification_source_text(firm), firm_name=firm.name)
        firm.classification = result.classification
        firm.classification_evidence = result.evidence
        if result.evidence_span:
            firm.blind_spots = (firm.blind_spots or "") + f" Classification evidence span: {result.evidence_span!r}"

    # Evidence Class B (2026-07-26): if the firm still has no classification and no
    # evidence_class, try search snippets directly — a third-party published description that
    # names the firm and describes it as a family office is affirmative evidence on its own,
    # not just a means of finding a website to fetch.
    if firm.classification.value == "Unable to Determine" and not firm.evidence_class and use_websearch_fallback:
        snippet_result = classify_from_search_snippets(firm.name, firm.hq_city)
        if snippet_result:
            firm.classification = snippet_result["classification"]
            firm.classification_evidence = snippet_result["evidence"]
            firm.classification_source_url = snippet_result["source_url"]
            firm.evidence_class = "B"
            firm.evidence_class_detail = f'Search snippet evidence: {snippet_result["evidence_span"]!r} ({snippet_result["source_url"]})'

    # Same evidence-class fix as enrichment/pipeline.py::qualifying() (2026-07-26): a firm with
    # affirmative evidence it IS a family office qualifies even if SFO/MFO subtype is
    # genuinely Unable to Determine — those are different questions, and subtype is never
    # guessed to force a qualifying outcome.
    qualifies = firm.classification.value != "Unable to Determine" or bool(firm.evidence_class)
    outcome = "qualifying" if qualifies else "unable_to_determine"
    return {"candidate_id": record.candidate_id, "outcome": outcome, "firm": firm.model_dump()}


def _process_one_safe(record, use_websearch_fallback: bool, stop_event: threading.Event) -> tuple[str, dict | None, Exception | None]:
    """Wraps process_one for use inside a worker thread. Returns
    (name, result_or_None, exception_or_None) instead of raising, so the pool driver loop
    (which is the only place that should print/append/decide whether to stop) stays simple."""
    if stop_event.is_set():
        return record.name_as_found, None, None
    try:
        result = process_one(record, use_websearch_fallback=use_websearch_fallback)
        return record.name_as_found, result, None
    except SearchBlocked as e:
        stop_event.set()
        return record.name_as_found, None, e
    except Exception as e:
        return record.name_as_found, None, e


def main(limit: int | None = None, use_websearch_fallback: bool = True, workers: int = 8) -> None:
    """Parallelized: this pipeline is I/O-bound (network fetch + LLM inference roundtrips
    dominate; per-candidate CPU work is negligible), so a thread pool gives a large wall-clock
    win without any change to per-candidate logic. The append-and-skip-done-ids design
    (PROGRESS_PATH) already made partial runs safe before this change, so parallelizing is
    low-risk on top of it — the only new invariant needed is a single writer lock (see
    _append()) so concurrent completions can't interleave/corrupt the progress file.

    Per-host throttling (SEC's fetch calls, the 3s DuckDuckGo spacing) is unaffected — those
    limits live inside enrichment/fetch.py and discovery/websearch.py's own request functions,
    which is the right layer: it caps how fast any one host gets hit regardless of how many
    threads are calling it, not how many candidates run concurrently overall."""
    candidates = load_candidates()
    done_ids = _load_done_ids()
    todo = [c for c in candidates if c.candidate_id not in done_ids]
    if limit:
        todo = todo[:limit]

    print(f"{len(candidates)} total candidates, {len(done_ids)} already done, "
          f"{len(todo)} to process this run. websearch_fallback={use_websearch_fallback}, "
          f"workers={workers}", flush=True)

    stop_event = threading.Event()
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_process_one_safe, record, use_websearch_fallback, stop_event): record
            for record in todo
        }
        for future in as_completed(futures):
            record = futures[future]
            name, result, err = future.result()
            completed += 1

            if isinstance(err, SearchBlocked):
                print(f"\nSTOPPING: {err}\n"
                      f"{completed}/{len(todo)} processed this run before the search backend "
                      f"blocked us. Nothing false was written for the candidate in progress — "
                      f"re-run later and it will resume from here, since progress already "
                      f"written to {PROGRESS_PATH} is skipped on the next run.", flush=True)
                for f in futures:
                    f.cancel()
                break
            if err is not None:
                # A crash on one candidate must not take down the run (confirmed 2026-07-26:
                # an unhandled JSONDecodeError killed a whole process before this existed).
                # Not marked done, so it's retried on the next invocation.
                print(f"[{completed}/{len(todo)}] {name[:50]:<50} -> ERROR: {type(err).__name__}: {err}", flush=True)
                continue
            if result is None:
                continue  # stop_event was already set before this one started

            _append(result)
            print(f"[{completed}/{len(todo)}] {name[:50]:<50} -> {result['outcome']}", flush=True)


if __name__ == "__main__":
    no_search = "--no-search" in sys.argv
    positional = [a for a in sys.argv[1:] if a != "--no-search"]
    limit_arg = int(positional[0]) if positional else None
    main(limit=limit_arg, use_websearch_fallback=not no_search)
