"""Scoped run: website resolution + classification for non-ADV candidates only (13F, Form D,
ProPublica, Wikidata) — ADV is already known-good from the last full run and doesn't need
re-processing. Uses the same per-candidate logic as enrichment/run_full.py but filtered to
non-ADV sources, with the new dual-backend search (DDG + Marginalia fallback) now available.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from enrichment.run_full import _process_one_safe, DETERMINISTIC_ENRICHERS
from discovery.store import load_candidates
import threading

OUT_PATH = Path("data/interim/nonadv_progress.jsonl")


def main(workers: int = 8):
    candidates = [c for c in load_candidates() if c.discovery_source != "SEC Form ADV Bulk Data"]
    done_ids = set()
    if OUT_PATH.exists():
        with OUT_PATH.open(encoding="utf-8") as f:
            for line in f:
                done_ids.add(json.loads(line)["candidate_id"])
    todo = [c for c in candidates if c.candidate_id not in done_ids]
    print(f"{len(candidates)} non-ADV candidates, {len(done_ids)} already done, {len(todo)} to process", flush=True)

    stop_event = threading.Event()
    lock = threading.Lock()
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_process_one_safe, r, True, stop_event): r for r in todo}
        for future in as_completed(futures):
            name, result, err = future.result()
            completed += 1
            if err is not None:
                print(f"[{completed}/{len(todo)}] {name[:50]:<50} -> ERROR/BLOCKED: {err}", flush=True)
                continue
            if result is None:
                continue
            with lock:
                with OUT_PATH.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(result, default=str) + "\n")
                    f.flush()
            print(f"[{completed}/{len(todo)}] {name[:50]:<50} -> {result['outcome']}", flush=True)

    print("DONE")


if __name__ == "__main__":
    main()
