"""Generic fetch layer: URL in, clean text + provenance metadata out.

One path for every source type. No per-site parsing lives here — that was
the mistake in the original proposal. This module's only job is
"get the bytes, get readable text out of them, record how and when."
Structured extraction (regex/selectors for known-structured sources,
an LLM call for everything else) happens downstream in enrichment/extract.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
import requests_cache

USER_AGENT = "FamilyOfficeResearchProject research-assessment@example.com"

# Transparent HTTP cache (2026-07-26): lexicon/classifier iteration needs to run many times
# against the same fetched pages without re-hitting the network each time. requests_cache was
# already a listed dependency but never wired in — a session-level cache means the first fetch
# of a URL pays the network cost once, and every classifier-tuning iteration after that is a
# cache hit (no network, no wait). 24h expiry: long enough for a tuning session, short enough
# not to go stale across days.
_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "interim" / "http_cache"
_session = requests_cache.CachedSession(str(_CACHE_PATH), expire_after=60 * 60 * 24)

_TAG_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
# UI-chrome guard (2026-07-26, added after the Element Pointe finding: a classifier match
# inside a contact-form dropdown — "Do you have a single-family office today? Select an
# option Yes No" — was stored as if the firm had said it about itself). form/nav/footer
# content is never the firm describing its own business; it's UI chrome (dropdown options,
# nav labels, boilerplate footer links) that happens to contain a marker phrase. Stripped out
# entirely before the classifier ever sees the text, rather than trusting the classifier to
# tell chrome apart from prose after the fact.
_CHROME_TAG_RE = re.compile(r"<(form|nav|footer)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


@dataclass
class FetchResult:
    url: str
    raw: str  # untouched response body — used for evidence-span grepping (e.g. Cloudflare-obfuscated emails)
    text: str  # tag-stripped, human-readable text — used as LLM extraction input
    fetched_at: str
    status_code: int
    content_type: str


def fetch(url: str, timeout: int = 20) -> FetchResult:
    resp = _session.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    raw = resp.text
    content_type = resp.headers.get("Content-Type", "")

    if "html" in content_type or raw.lstrip().startswith("<"):
        text = _TAG_RE.sub(" ", raw)
        text = _CHROME_TAG_RE.sub(" ", text)
        text = _ANY_TAG_RE.sub(" ", text)
        text = _WS_RE.sub(" ", text)
        text = _BLANKLINES_RE.sub("\n\n", text)
        text = "\n".join(line.strip() for line in text.splitlines())
        text = re.sub(r"\n{2,}", "\n", text).strip()
    else:
        text = raw

    return FetchResult(
        url=url,
        raw=raw,
        text=text,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        status_code=resp.status_code,
        content_type=content_type,
    )
