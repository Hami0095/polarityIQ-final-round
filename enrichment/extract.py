"""Structured extraction: fetched text -> SourcedField values, against a
fixed schema. Deterministic parsing (regex/selectors/JSON fields) is used
wherever a source is reliably structured (EDGAR XML, ProPublica JSON).
extract_with_llm() is the generic path for everything else (firm websites,
press articles) — it is a real call to the Anthropic API made from inside
this program, not a value typed in by a human mid-conversation. That is the
actual fix for the provenance problem: the model moved inside the program,
where its input/output is logged and re-runnable, instead of being the
runtime itself.

Every value returned by either path must come with an evidence_span — the
literal snippet of source text it was drawn from — so validation can reject
anything not actually supported by the source. See SourcedField in
dataset/schema.py and the Real Capital Solutions incident in DECISIONS.md.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date

import requests
from rapidfuzz import fuzz

from dataset.schema import Confidence, SourcedField

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# minimax-m3:cloud was the first choice (user-specified) but fabricated values on 3/3 test
# runs against a real firm page — invented an AUM figure twice with no real evidence_span, and
# paraphrased a description instead of quoting it. The evidence-span gate caught every one of
# those, so nothing false shipped, but usable yield was ~0. gpt-oss:120b-cloud, tested on the
# identical page, returned every field correctly with a literal, verified evidence_span. See
# DECISIONS.md 2026-07-25. minimax-m3:cloud remains available via OLLAMA_MODEL if needed.
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")

EXTRACTION_SCHEMA_FIELDS = [
    "description", "investment_thesis", "sectors", "aum",
    "hq_city", "hq_state", "hq_country",
    "firm_email", "firm_phone",
]

# Field-type gating (2026-07-26 fix): the anti-fabrication check requires value to be a literal
# substring of the source text. That's correct and strong for ATOMIC fields (a phone number,
# a city name — there's one right way to copy them). It is impossible by construction for PROSE
# fields if the model is asked to "describe" or "summarize" the firm, since any summary is a
# paraphrase, not a substring, and would always get rejected — that was silently zeroing out
# yield on every prose field regardless of model or prompt quality (confirmed 2026-07-26: real,
# accurate summaries were being discarded alongside fabricated ones). Fix: for prose fields,
# stop asking the model to summarize — ask it to SELECT a verbatim sentence or two, copied
# exactly, that best describes the firm/thesis/sectors. The substring check then passes by
# construction for a genuine selection, and the field ends up holding the firm's own words with
# a real source, which is more defensible than a paraphrase anyway.
PROSE_FIELDS = {"description", "investment_thesis", "sectors"}
ATOMIC_FIELDS = {"aum", "hq_city", "hq_state", "hq_country", "firm_email", "firm_phone"}

EXTRACTION_PROMPT = """You are extracting structured facts about a family office or wealth \
management firm from the text below, which was fetched from {url} on {fetched_at}.

Return ONLY valid JSON, no prose, matching this exact shape:
{{
  "description": {{"value": "...", "evidence_span": "literal quote from the text"}} or null,
  "investment_thesis": {{"value": "...", "evidence_span": "..."}} or null,
  "sectors": {{"value": "...", "evidence_span": "..."}} or null,
  "aum": {{"value": "...", "evidence_span": "..."}} or null,
  "hq_city": {{"value": "...", "evidence_span": "..."}} or null,
  "hq_state": {{"value": "...", "evidence_span": "..."}} or null,
  "hq_country": {{"value": "...", "evidence_span": "..."}} or null,
  "firm_email": {{"value": "...", "evidence_span": "..."}} or null,
  "firm_phone": {{"value": "...", "evidence_span": "..."}} or null
}}

Rules, non-negotiable:
- For "description", "investment_thesis", and "sectors": do NOT summarize or paraphrase.
  SELECT the single sentence (or short run of consecutive sentences) from the SOURCE TEXT below
  that most directly answers the field, and copy it VERBATIM, character-for-character, as the
  "value" itself. The "value" and "evidence_span" should be the same text (or evidence_span may
  be that same quote with a little more surrounding context). If no sentence in the source text
  answers the field, return null — do not construct a summary sentence of your own.
- For "aum", "hq_city", "hq_state", "hq_country", "firm_email", "firm_phone": extract the exact
  value as it literally appears (a phone number, a city name, a dollar figure) — these should
  still be copied exactly, not reformatted.
- evidence_span MUST be copied character-for-character out of the SOURCE TEXT below — the same
  spacing, capitalization, and punctuation as it appears. Do not combine text from two different
  places into one span. It will be checked by exact substring match against the source text
  below, and if it does not match exactly, the field will be discarded. If you cannot find a
  real verbatim span for a value, set both value and evidence_span to null for that field rather
  than approximate one.
- Never infer, construct, or pattern-generate a contact value (e.g. never build
  firstname.lastname@domain from a name and a domain). Only extract an email/phone if it
  appears literally, character for character, in the source text.
- If the text does not support a field, return null for it. Nulls are expected and fine.
- aum should be a short value like "$1.2B" with the as-of context if stated; do not convert
  13F/AUM-adjacent regulatory holdings figures into an AUM claim.

SOURCE TEXT:
---
{text}
---

Return only the JSON object.
"""


def _ollama_chat(prompt: str, model: str) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
            timeout=300,
        )
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_URL}. extract_with_llm() requires a real, "
            "running model call from inside the program (Correction 1) — there is no fallback "
            "that fabricates or stands in for this. Start `ollama serve` (or set OLLAMA_URL) "
            "and re-run enrichment for unstructured-page fields; deterministic sources "
            "(EDGAR/ProPublica) do not need it."
        ) from e
    data = resp.json()
    return data["message"]["content"]


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _best_matching_sentence(claimed_value: str, source_text: str, min_len: int = 15) -> tuple[str | None, float]:
    """Split source_text into sentence-ish chunks and return the one most similar to
    claimed_value (rapidfuzz token_sort_ratio, robust to word-order-preserving typos like a
    stray space) along with its score. Only chunks of reasonable length are considered, so a
    one-word nav fragment can't "win" by fuzzy-matching a long claimed sentence."""
    chunks = [c.strip() for c in _SENTENCE_SPLIT_RE.split(source_text) if len(c.strip()) >= min_len]
    if not chunks:
        return None, 0.0
    best_chunk, best_score = None, 0.0
    for chunk in chunks:
        score = fuzz.token_sort_ratio(claimed_value.lower(), chunk.lower())
        if score > best_score:
            best_chunk, best_score = chunk, score
    return best_chunk, best_score


def extract_with_llm(text: str, url: str, fetched_at: str, model: str = OLLAMA_MODEL) -> dict[str, SourcedField]:
    # Tried reordering fetched text to put long/substantive lines first, on the theory the
    # model was defaulting to the page's title line (2026-07-26). Tested against a page with
    # real body prose (arrowrootfamilyoffice.com): it made results WORSE, not better — the
    # model concatenated a much larger blob and began fabricating fragments inside it (a
    # garbled firm name, nonsense trailing text), which the evidence gate correctly rejected,
    # yielding nothing instead of the smaller-but-real title it returned before. Reverted.
    # This is a real, current yield ceiling with this model/prompt on real small-firm pages,
    # not a bug with an available cheap fix — documented rather than chased further given the
    # time budget.
    prompt = EXTRACTION_PROMPT.format(url=url, fetched_at=fetched_at, text=text[:15000])

    raw = _ollama_chat(prompt, model).strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise json.JSONDecodeError("expected a JSON object", raw, 0)
    except json.JSONDecodeError:
        # Documented failure mode (DECISIONS.md): malformed model output yields zero fields,
        # exactly like an unsupported evidence_span does — it must NOT crash the caller. A
        # crash here previously took down an entire multi-hour pipeline run over one bad
        # response from one candidate (2026-07-26).
        return {field_name: SourcedField(confidence=Confidence.NONE) for field_name in EXTRACTION_SCHEMA_FIELDS}

    text_norm = " ".join(text.split()).lower()
    text_collapsed = " ".join(text.split())  # same whitespace collapsing, original case kept

    out: dict[str, SourcedField] = {}
    for field_name in EXTRACTION_SCHEMA_FIELDS:
        item = data.get(field_name)
        # The model occasionally returns a field as a bare string/list instead of the
        # requested {"value":..., "evidence_span":...} object (confirmed 2026-07-26, STOKES
        # FAMILY OFFICE LLC: crashed run_full.py's per-candidate handling with
        # AttributeError before the outer catch-and-continue was added). Treat anything that
        # isn't a dict as "no usable value" rather than trusting its shape.
        if not isinstance(item, dict) or not item.get("value"):
            out[field_name] = SourcedField(confidence=Confidence.NONE)
            continue
        value = item["value"]
        if not isinstance(value, str):
            value = str(value)
        model_span = item.get("evidence_span") or ""

        # Anti-fabrication check, derived from the real source text rather than trusted from
        # the model. Originally this required the MODEL to echo back a matching quote
        # (value-in-span + span-in-source, both model-reported) — but gpt-oss:120b-cloud
        # proved unreliable at formatting that quote correctly even when the underlying value
        # was itself real and present on the page (confirmed 2026-07-26: description/hq_city/
        # phone values that were genuinely on mactaggartfp.com came back with evidence_span
        # null or empty across repeated attempts, so real, correct extractions were being
        # discarded along with fabricated ones — the model's span-FORMATTING reliability was
        # gating real yield, not the model's factual accuracy).
        #
        # Fix: search for the model's claimed VALUE directly in the actual fetched text
        # ourselves, and derive evidence_span as a real window of source text around that
        # match — the model no longer has to produce a matching quote at all. This is
        # STRICTER against fabrication than the original two-part check, not looser: a
        # fabricated value with a fabricated-but-plausible span could theoretically have
        # slipped through the old check if the span also happened to appear verbatim
        # somewhere; this version requires the VALUE ITSELF to be a literal substring of the
        # real document, full stop.
        value_norm = value.strip().lower()
        supported = bool(value_norm) and value_norm in text_norm
        span = None
        if supported:
            idx = text_norm.index(value_norm)
            start = max(0, idx - 60)
            end = min(len(text_collapsed), idx + len(value_norm) + 60)
            span = text_collapsed[start:end]
        elif field_name in PROSE_FIELDS and value_norm:
            # Fuzzy-match fallback for prose fields only (2026-07-26): the model reliably picks
            # the RIGHT sentence but sometimes introduces a small transcription slip (confirmed:
            # "Arrow Root" for "Arrowroot", a single inserted space) that fails an exact
            # substring check even though it selected genuine content, not a fabrication. Atomic
            # fields (phone/email/city/etc.) get NO such leniency — there's no excuse for a
            # transcription error on a value with one correct form, so they stay on the strict
            # exact-substring check above. For prose, use the model's value only as a SEARCH KEY
            # to locate the right real sentence via fuzzy match, then use the ACTUAL source
            # sentence — never the model's copy — as both value and evidence_span. This can only
            # ever produce genuine source text, regardless of how the model mangled its own
            # transcription.
            real_sentence, score = _best_matching_sentence(value, text_collapsed)
            if real_sentence and score >= 85:
                value = real_sentence
                span = real_sentence
                supported = True
        if not supported and model_span:
            span = model_span  # kept for audit visibility even though value is rejected

        out[field_name] = SourcedField(
            value=value if supported else None,
            source_url=url,
            verification_method=f"LLM extraction ({model}, in-program via Ollama) against fetched source text",
            confidence=Confidence.MEDIUM if supported else Confidence.NONE,
            checked_at=date.today().isoformat(),
            evidence_span=span or None,  # kept even when unsupported, for audit visibility
            fetched_at=fetched_at,
            source_doc_len=len(text),
        )
    return out
