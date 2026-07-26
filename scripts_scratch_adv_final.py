from __future__ import annotations
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from discovery.store import load_candidates
from enrichment.run_full import process_one

cands = [c for c in load_candidates() if c.discovery_source == "SEC Form ADV Bulk Data"]
print(len(cands), "ADV candidates", flush=True)
qual = []
with ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(process_one, c, False): c for c in cands}
    for i, future in enumerate(as_completed(futures), 1):
        c = futures[future]
        try:
            r = future.result()
        except Exception as e:
            print(f"[{i}/{len(cands)}] {c.name_as_found[:40]:<40} ERROR {e}", flush=True)
            continue
        print(f"[{i}/{len(cands)}] {c.name_as_found[:40]:<40} -> {r['outcome']}", flush=True)
        if r["outcome"] == "qualifying":
            qual.append(r)

print("qualifying:", len(qual), flush=True)
with open("data/interim/adv_qualifying.jsonl", "w", encoding="utf-8") as f:
    for r in qual:
        f.write(json.dumps(r, default=str) + "\n")
print("DONE", flush=True)
