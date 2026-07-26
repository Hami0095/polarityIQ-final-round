"""Fetch subpaths for every candidate that ALREADY resolved a website in the just-completed
full run (per pipeline_progress.jsonl's firm.website field) — no re-guessing needed, that's a
separate step. Caches combined raw text per candidate to
data/interim/candidate_raw_text.json for instant, network-free classifier-lexicon iteration.
"""
from __future__ import annotations

import json
from pathlib import Path

from enrichment.fetch import fetch

SUBPATHS = ("", "about/", "about-us/", "who-we-are/", "team/", "firm/", "our-firm/")
OUT_PATH = Path("data/interim/candidate_raw_text.json")
PROGRESS_PATH = Path("data/interim/pipeline_progress.jsonl")


def main():
    resolved: dict[str, dict] = {}
    with PROGRESS_PATH.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if "firm" not in r:
                continue
            website = r["firm"].get("website")
            if website:
                resolved[r["candidate_id"]] = {"name": r["firm"]["name"], "url": website}

    print(f"{len(resolved)} candidates with a resolved website from the last run")

    out: dict[str, dict] = {}
    if OUT_PATH.exists():
        out = json.loads(OUT_PATH.read_text(encoding="utf-8"))

    for i, (cid, info) in enumerate(resolved.items(), 1):
        if cid in out:
            continue
        url = info["url"]
        texts = []
        for path in SUBPATHS:
            page_url = url.rstrip("/") + "/" + path if path else url
            try:
                r = fetch(page_url)
                texts.append(r.text)
            except Exception:
                continue
        out[cid] = {"name": info["name"], "url": url, "text": "\n".join(texts)}
        print(f"[{i}/{len(resolved)}] {info['name'][:50]:<50} -> {len(out[cid]['text'])} chars", flush=True)
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(out, indent=0), encoding="utf-8")  # incremental save
    print(f"DONE: {len(out)} candidates cached, "
          f"{sum(1 for v in out.values() if v['text'])} with real text")


if __name__ == "__main__":
    main()
