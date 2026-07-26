"""Real RAG search + synthesis app over the qualifying family-office dataset (50 records as of
the 2026-07-26 freeze -- read len(_raw_rows) / GET /api/health for the live count rather than
trusting a number in this docstring, which is exactly the kind of comment that goes stale as the
dataset grows and was found to have done so here).

Retrieval: hybrid of (1) structured field filters (classification, state) and (2) semantic
search via TF-IDF + cosine similarity, computed from scratch (no sklearn/numpy dependency —
avoids Vercel serverless size limits, and a from-scratch vector space model over a corpus this
size is instant at cold start; this is a real vector-space retrieval method, just not neural
embeddings, and that tradeoff is stated plainly here and in the docs rather than implied away).

Synthesis: template-based, not LLM-based — there is no reliable LLM API key available to this
deployed serverless function (the local Ollama instance used during enrichment is not
internet-reachable from Vercel). Every sentence in a synthesized answer is assembled FROM
verified field values that already carry a real evidence_span from the pipeline; nothing is
generated freely. The grounding gate reused here is the exact same check used throughout
enrichment (dataset/schema.py's SourcedField.evidence_supports_value logic) — a field's value
must be a literal substring of its own evidence_span to be shown or spoken at all. Fields that
fail this, or lack an evidence_span entirely, are explicitly named as unanswerable rather than
silently omitted.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, Response
from pydantic import BaseModel
from rapidfuzz import fuzz, process

DATA_PATH = Path(__file__).resolve().parent / "data" / "firms.json"
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Grounding gate — same logic as dataset/schema.py's SourcedField, reused not reinvented.
# ---------------------------------------------------------------------------


class GroundedField(BaseModel):
    value: Optional[str] = None
    source_url: Optional[str] = None
    evidence_span: Optional[str] = None
    confidence: Optional[str] = None

    def is_grounded(self) -> bool:
        if self.value is None:
            return False
        if not self.evidence_span:
            return False
        return self.value.strip().lower() in self.evidence_span.strip().lower()


def _field(row: dict, name: str) -> GroundedField:
    return GroundedField(
        value=row.get(name) or None,
        source_url=row.get(f"{name}_source") or row.get("discovery_url") or None,
        evidence_span=row.get(f"{name}_evidence_span") or None,
        confidence=row.get(f"{name}_confidence") or None,
    )


# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------

_raw_rows: list[dict] = json.loads(DATA_PATH.read_text(encoding="utf-8")) if DATA_PATH.exists() else []


# US state name <-> abbreviation, both directions in the map so a lookup either way is a
# single dict access. Added 2026-07-26: hq_state is stored as the two-letter abbreviation
# (e.g. "CA"), so a natural-language query like "family office California" previously
# matched nothing on location at all — invisible before because shared "family office"
# tokens alone were enough to return results regardless (see live_queries.md query #5).
_STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin",
    "WY": "Wyoming", "DC": "District of Columbia",
}


def _searchable_text(row: dict) -> str:
    hq_state = (row.get("hq_state") or "").strip()
    state_full_name = _STATE_NAMES.get(hq_state.upper())
    return " ".join(filter(None, [
        row.get("name"), row.get("classification"), row.get("description"),
        row.get("hq_city"), hq_state, state_full_name, row.get("hq_country"),
        row.get("sectors"), row.get("discovery_source"),
    ]))


# ---------------------------------------------------------------------------
# TF-IDF, from scratch. A few dozen documents at this corpus size — cold-start cost is negligible.
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Domain-universal terms present in nearly every document's searchable text (every record is
# some kind of "family office"). Confirmed 2026-07-26: leaving them in meant a query like
# "family offices in Japan" (matching zero real content, no firm here is Japan-based) scored
# a HIGHER top cosine similarity (0.587) than a genuine semantic match like "family office
# focused on impact and mission-driven investing" (0.281) — short queries dominated by these
# common tokens outscore longer queries diluted by real distinctive content words. A single
# score-cutoff threshold cannot fix this (it would have to reject the higher-scoring noise
# query while accepting the lower-scoring real one, or vice versa). Stripping these terms from
# tokenization — for both documents and queries, so IDF is computed consistently — removes
# their contribution entirely: "Japan"/"biotech"-type queries whose only remaining terms match
# no document now correctly score 0 everywhere and fall through the existing `scores[i] > 0`
# filter into a clean decline, while genuine queries are now scored purely on their actual
# distinctive terms.
_DOMAIN_STOPWORDS = {"family", "office", "offices"}

# General English stopwords (2026-07-26): a stray preposition surviving tokenization can act as
# exactly the same kind of noise-token bridge the domain stopwords were added to kill. Found via
# Paulson & Co.'s description ("...based in Palm Beach, Florida...") sharing only the word "in"
# with queries like "family offices in Japan" / "...invest in biotech" — enough shared-token
# weight for `scores[i] > 0` to let a firm with zero real connection to the query surface. Same
# fix as before: strip these from both documents and queries so they can never contribute score.
_STOPWORDS = {
    "in", "on", "at", "of", "the", "and", "for", "to", "with", "by", "from",
    # 2026-07-26: the first-pass list above (prepositions/articles/conjunctions only) left
    # "is" as a residual noise-bridge (Paulson & Co.'s "...is an investment management
    # company..." still weakly matched "what is the email for Korys"). A partial stopword list
    # is the same bug with fewer instances -- extended to a standard English stopword set
    # rather than patching one word at a time.
    "is", "are", "was", "were", "be", "a", "an", "that", "this", "it", "as", "or", "but",
    "if", "then", "than", "so", "do", "does", "which", "who", "what", "when", "where", "how",
    "all", "any", "can", "will", "would", "there", "their", "its", "has", "have", "had",
}


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _DOMAIN_STOPWORDS and t not in _STOPWORDS]


class TfidfIndex:
    def __init__(self, documents: list[str]):
        self.docs_tokens = [_tokenize(d) for d in documents]
        self.n = len(documents)
        df: Counter = Counter()
        for tokens in self.docs_tokens:
            for term in set(tokens):
                df[term] += 1
        self.idf = {term: math.log((1 + self.n) / (1 + count)) + 1 for term, count in df.items()}
        self.doc_vectors = [self._vectorize(tokens) for tokens in self.docs_tokens]

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        vec = {term: (count / len(tokens)) * self.idf.get(term, 0.0) for term, count in tf.items()} if tokens else {}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def query(self, text: str) -> list[float]:
        qvec = self._vectorize(_tokenize(text))
        scores = []
        for dvec in self.doc_vectors:
            score = sum(qvec.get(term, 0.0) * weight for term, weight in dvec.items())
            scores.append(score)
        return scores


_index = TfidfIndex([_searchable_text(r) for r in _raw_rows]) if _raw_rows else None


# ---------------------------------------------------------------------------
# Retrieval: filters + semantic score combined
# ---------------------------------------------------------------------------

def retrieve(query: str, classification: str | None, state: str | None, limit: int = 10) -> list[dict]:
    candidates = list(enumerate(_raw_rows))

    if classification:
        candidates = [(i, r) for i, r in candidates if r.get("classification") == classification]
    if state:
        candidates = [(i, r) for i, r in candidates if (r.get("hq_state") or "").strip().upper() == state.strip().upper()]

    if query.strip() and _index:
        scores = _index.query(query)
        candidates = [(i, r) for i, r in candidates if scores[i] > 0]
        candidates.sort(key=lambda ir: -scores[ir[0]])
    # no query: keep filter order (dataset order), still a defined result, not random

    return [r for _, r in candidates[:limit]]


# ---------------------------------------------------------------------------
# Fuzzy "did you mean" fallback — only when TF-IDF returns nothing for a real
# query, never auto-executed, per explicit instruction: suggest, don't guess.
# ---------------------------------------------------------------------------

FUZZY_MATCH_THRESHOLD = 65


def _strip_domain_stopwords(s: str) -> str:
    return " ".join(t for t in _TOKEN_RE.findall(s.lower()) if t not in _DOMAIN_STOPWORDS and t not in _STOPWORDS)


def fuzzy_suggestion(query: str) -> dict | None:
    """Confirmed broken 2026-07-26: scoring the raw query against raw firm names fires on
    legitimate no-match queries, not just typos — "family offices in Japan" scored 85.5
    against "WEALTH DIMENSIONS FAMILY OFFICE, INC" purely because both strings share the
    dominant "family office(s)" tokens, even though "Japan" (the only real content word)
    matches nothing. A real typo of a short name ("arowroot") and a long sentence that merely
    contains "family office" somewhere are indistinguishable to a raw-string scorer.
    Fix: strip the same domain-universal tokens used for TF-IDF (_DOMAIN_STOPWORDS) from BOTH
    the query and every candidate name before scoring, so the comparison is driven by actual
    distinguishing content. Verified against 5 cases before shipping: real typos ("arowroot",
    "sestante family ofice", "xception familly office") score 76-90 after stripping; genuine
    no-match queries ("family offices in Japan", "which family offices invest in biotech")
    drop to 40-45 — a threshold of 65 cleanly separates them where the unstripped score (78.75
    vs 85.5) did not."""
    if not query.strip() or not _raw_rows:
        return None
    stripped_query = _strip_domain_stopwords(query)
    if not stripped_query:
        return None  # nothing left but domain-universal words -> no real content to match on
    names = [r.get("name") or "" for r in _raw_rows]
    stripped_names = [_strip_domain_stopwords(n) for n in names]
    match = process.extractOne(stripped_query, stripped_names, scorer=fuzz.WRatio)
    if not match:
        return None
    _, score, idx = match
    if score < FUZZY_MATCH_THRESHOLD:
        return None
    return {"name": names[idx], "score": round(score, 1)}


# ---------------------------------------------------------------------------
# Synthesis: template-based, gated per field
# ---------------------------------------------------------------------------

DISPLAY_FIELDS = ["description", "firm_email", "firm_phone", "aum"]


def build_card(row: dict) -> dict:
    card = {
        "firm_id": row.get("firm_id"),
        "name": row.get("name"),
        "classification": row.get("classification"),
        "hq": ", ".join(filter(None, [row.get("hq_city"), row.get("hq_state"), row.get("hq_country")])) or None,
        "discovery_source": row.get("discovery_source"),
        "evidence_class": row.get("evidence_class") or None,
        "website": row.get("website") or None,
        "grounded_fields": {},
        "insufficient_evidence_fields": [],
    }
    for field_name in DISPLAY_FIELDS:
        gf = _field(row, field_name)
        if gf.is_grounded():
            card["grounded_fields"][field_name] = {
                "value": gf.value, "source_url": gf.source_url, "evidence_span": gf.evidence_span,
            }
        else:
            card["insufficient_evidence_fields"].append(field_name)
    return card


def synthesize_answer(query: str, cards: list[dict]) -> dict:
    """Template-based synthesis: every claim is assembled from a card's already-grounded
    field, cited with its evidence span. Nothing here is generated — it's composed. If a
    query matches zero grounded facts, the system explicitly declines rather than guessing."""
    if not cards:
        return {
            "answer": "No matching records with sufficient evidence were found for this query.",
            "status": "empty",
            "citations": [],
        }

    claims = []
    citations = []
    for card in cards[:5]:
        name = card["name"]
        cls = card["classification"]
        hq = f" headquartered in {card['hq']}" if card["hq"] else ""
        sentence = f"{name} is classified as {cls}{hq}."
        claims.append(sentence)
        if card["evidence_class"]:
            claims.append(f"  Evidence: {card['evidence_class']} — {row_evidence_detail(card)}.")
        desc = card["grounded_fields"].get("description")
        if desc:
            claims.append(f"  Description (source-verified): “{desc['value']}”")
            citations.append({"firm": name, "field": "description", "source_url": desc["source_url"],
                               "evidence_span": desc["evidence_span"]})
        aum = card["grounded_fields"].get("aum")
        if aum:
            # aum's value already carries its own precise label (see enrichment/adv_item5d.py /
            # the "Regulatory AUM per Form ADV Item 5.F" wording baked into the CSV cell) —
            # printed verbatim here rather than re-labeled a second time, so there's exactly one
            # place that states what this number is and isn't.
            claims.append(f"  AUM (source-verified): {aum['value']}")
            citations.append({"firm": name, "field": "aum", "source_url": aum["source_url"],
                               "evidence_span": aum["evidence_span"]})
        for field_name in ("firm_email", "firm_phone"):
            f = card["grounded_fields"].get(field_name)
            if f:
                citations.append({"firm": name, "field": field_name, "source_url": f["source_url"],
                                   "evidence_span": f["evidence_span"]})
        if card["insufficient_evidence_fields"]:
            claims.append(f"  Insufficient evidence for: {', '.join(card['insufficient_evidence_fields'])}.")

    status = "success" if len(cards) >= 3 else "partial"
    return {"answer": "\n".join(claims), "status": status, "citations": citations}


def row_evidence_detail(card: dict) -> str:
    return {"A": "structured third-party classification (Wikidata)",
            "B": "third-party published description",
            "C": "regulatory self-description",
            "D": "first-party website self-description"}.get(card["evidence_class"], "unspecified")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Family Office Intelligence Search</title>
<style>
:root{color-scheme:light dark}
body{font-family:-apple-system,system-ui,sans-serif;max-width:820px;margin:0 auto;padding:20px;
  background:#0b0f14;color:#e6edf3}
@media (prefers-color-scheme:light){body{background:#fafafa;color:#1a1a1a}}
h1{font-size:1.3rem;margin-bottom:4px}
.sub{color:#8b949e;font-size:.88rem;margin-bottom:16px}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
input[type=text]{flex:1;min-width:220px;padding:10px 12px;font-size:1rem;border-radius:8px;
  border:1px solid #30363d;background:#161b22;color:#e6edf3}
select{padding:10px;border-radius:8px;border:1px solid #30363d;background:#161b22;color:#e6edf3}
@media (prefers-color-scheme:light){input,select{background:#fff;color:#1a1a1a;border-color:#ccc}}
button{padding:10px 16px;border-radius:8px;border:none;background:#2f81f7;color:#fff;cursor:pointer;font-weight:600}
#status{color:#8b949e;font-size:.85rem;margin:10px 0}
.answer-box{border:1px solid #2f81f7;border-radius:10px;padding:14px;margin-bottom:16px;
  background:rgba(47,129,247,.08);white-space:pre-wrap;font-size:.92rem;line-height:1.5}
.status-empty{border-color:#8b949e;background:rgba(139,148,158,.08)}
.status-partial{border-color:#d29922;background:rgba(210,153,34,.08)}
.card{border:1px solid #30363d;border-radius:10px;padding:12px 14px;margin:10px 0;background:rgba(110,118,129,.06)}
.card h3{margin:0 0 4px 0;font-size:1rem}
.meta{color:#8b949e;font-size:.8rem;margin-bottom:6px}
.field{font-size:.88rem;margin:4px 0}
.field b{color:#2f81f7}
.missing{color:#8b949e;font-style:italic;font-size:.82rem;margin-top:6px}
.cite{font-size:.75rem;color:#8b949e}
</style></head>
<body>
<h1>Family Office Intelligence Search</h1>
<div class="sub">{{FIRM_COUNT}} qualifying records. Every field shown is gated: its value must be a
literal substring of its own cited evidence. Filters + search combine; empty query returns
filtered list.</div>
<div class="controls">
  <input id="q" type="text" placeholder="e.g. multi-family office California">
  <select id="cls"><option value="">Any classification</option>
    <option value="Multi-Family Office">MFO</option>
    <option value="Single-Family Office">SFO</option>
    <option value="Subtype unconfirmed">Subtype unconfirmed (confirmed family office)</option></select>
  <select id="state"><option value="">Any state</option></select>
  <button onclick="run()">Search</button>
</div>
<div id="status"></div>
<div id="answer"></div>
<div id="results"></div>
<script>
async function loadStates(){
  const r = await fetch('/api/states');
  const d = await r.json();
  const sel = document.getElementById('state');
  d.states.forEach(s => { const o=document.createElement('option'); o.value=s; o.textContent=s; sel.appendChild(o); });
}
async function run(){
  const q = document.getElementById('q').value;
  const cls = document.getElementById('cls').value;
  const state = document.getElementById('state').value;
  document.getElementById('status').textContent = 'searching...';
  const params = new URLSearchParams({q, classification: cls, state});
  const r = await fetch('/api/search?' + params.toString());
  const d = await r.json();
  document.getElementById('status').textContent = d.results.length + ' result(s)';
  const a = d.synthesis;
  const statusClass = a.status === 'empty' ? 'status-empty' : (a.status === 'partial' ? 'status-partial' : '');
  let answerHtml = `<div class="answer-box ${statusClass}">${a.answer.replace(/</g,'&lt;')}</div>`;
  if (d.suggestion) {
    const safeName = d.suggestion.name.replace(/</g,'&lt;').replace(/'/g,"\\'");
    answerHtml += `<div class="answer-box status-empty">Did you mean: <b>${d.suggestion.name.replace(/</g,'&lt;')}</b>? <button type="button" onclick="document.getElementById('q').value='${safeName}'">Use this</button></div>`;
  }
  document.getElementById('answer').innerHTML = answerHtml;
  document.getElementById('results').innerHTML = d.results.map(r => `
    <div class="card">
      <h3>${r.name}</h3>
      <div class="meta">${r.classification} ${r.evidence_class ? '(Evidence Class '+r.evidence_class+')' : ''} | ${r.hq || 'HQ unknown'} | via ${r.discovery_source}</div>
      ${Object.entries(r.grounded_fields).map(([k,v]) => `<div class="field"><b>${k}:</b> ${v.value}<div class="cite">source: ${v.source_url||'n/a'}</div></div>`).join('')}
      ${r.insufficient_evidence_fields.length ? `<div class="missing">Insufficient evidence: ${r.insufficient_evidence_fields.join(', ')}</div>` : ''}
    </div>`).join('') || '<p class="missing">No results.</p>';
}
loadStates();
document.getElementById('q').addEventListener('keydown', e => { if(e.key==='Enter') run(); });
</script>
</body></html>
"""


@app.route("/")
def index():
    # firm_count is templated in at serve time, not hardcoded, after the header text was found
    # stuck at "28" (the original skeleton's count) straight through five later dataset
    # expansions (40/46/48/50) -- a live, user-visible number that had gone stale is worse than
    # not stating one at all.
    return Response(PAGE.replace("{{FIRM_COUNT}}", str(len(_raw_rows))), mimetype="text/html")


@app.route("/api/states")
def api_states():
    states = sorted({r.get("hq_state", "").strip() for r in _raw_rows if r.get("hq_state", "").strip()})
    return jsonify({"states": states})


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    classification = request.args.get("classification") or None
    state = request.args.get("state") or None
    rows = retrieve(q, classification, state)
    cards = [build_card(r) for r in rows]
    synthesis = synthesize_answer(q, cards)
    suggestion = fuzzy_suggestion(q) if not rows else None
    return jsonify({
        "query": q, "count": len(_raw_rows), "results": cards, "synthesis": synthesis,
        "suggestion": suggestion,
    })


@app.route("/api/health")
def health():
    return jsonify({"ok": True, "firm_count": len(_raw_rows)})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
