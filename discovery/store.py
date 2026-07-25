"""Append-only candidate store. Every discovery connector writes here via
add_candidates() so the final methodology summary can be generated from
what actually ran, not hand-written afterward.
"""
from __future__ import annotations

import json
from pathlib import Path

from dataset.schema import DiscoveryRecord

CANDIDATES_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "candidates.jsonl"
RAW_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "discovery_log.jsonl"


def add_candidates(records: list[DiscoveryRecord], raw_payload: dict | None = None) -> None:
    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CANDIDATES_PATH.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")
    if raw_payload is not None:
        RAW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with RAW_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(raw_payload, default=str) + "\n")


def load_candidates() -> list[DiscoveryRecord]:
    if not CANDIDATES_PATH.exists():
        return []
    out = []
    with CANDIDATES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(DiscoveryRecord.model_validate_json(line))
    return out


def source_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in load_candidates():
        counts[c.discovery_source] = counts.get(c.discovery_source, 0) + 1
    return counts
