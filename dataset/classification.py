"""SFO / MFO / Unable-to-Determine classification, with the evidence span that drove it stored
on the Firm, not just a label. Runs AFTER entity_filter.check_entity_type() — a candidate that
fails the entity-type filter never reaches this step at all.

Explicit non-goal, stated because it's a real temptation: never infer SFO from a family surname
appearing in the entity name alone ("Danis Family Office, LLC" is not SFO evidence just because
it's named after a family — it needs affirmative text describing it as serving one family/that
family's own wealth). A name is a hypothesis, not evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from dataset.schema import Classification

# Affirmative language that a source describes the entity as serving ONE family's own wealth.
# Broadened 2026-07-26 with the shorter, more colloquial phrasings real small-firm sites
# actually use ("our family's", "the family we serve") alongside the more formal ones —
# the original list skewed toward press/legal register and was missing plainer first-party
# phrasing.
SFO_MARKERS: list[str] = [
    r"\bsingle[\s-]family office",
    r"\bfamily['’]?s own (wealth|assets|capital)",
    r"\b(manages|serves|for) (the )?[a-z]+ family['’]?s (wealth|assets|investments)",
    r"\bprivate (investment (office|vehicle)|family office) (of|for) (the )?[a-z]+ family",
    r"\bone family['’]?s (wealth|assets)",
    r"\bpersonal (family office|investment vehicle) of\b",
    r"\bour family['’]?s",
    r"\bone family\b",
    r"\bthe family we serve",
    r"\ba single family\b",
    r"\bfamily['’]?s (investments|capital)\b",
    r"\bestablished by the [a-z]+ family\b",
    r"\bserves? one family\b",
]
# Tried adding generic first-person "our family office" / "is a private family office" /
# "we are a family office" as weak SFO signals (2026-07-26) — reverted immediately.
# Confirmed false positives within the same test batch: "Innovative Family Office LLC"
# ("serves high-net-worth and ultra-high-net-worth investors" — clearly multi-client, no
# single-family language) and "Exceptional Wealth & Family Office" both got wrongly
# classified SFO purely off the generic self-description, with no actual single-family
# evidence backing it. Confirms the explicit warning that bare "family office" self-description
# is too weak alone — it was too weak even with the "our"/"we are" framing, not just the bare
# noun. Not used.

# Affirmative language that a source describes the entity as serving multiple, unrelated
# client families. Broadened 2026-07-26 with plainer phrasings ("client families", "families
# we serve", "our client families") alongside the more formal/numeric ones.
MFO_MARKERS: list[str] = [
    r"\bmulti[\s-]family office",
    r"\bmultifamily office",
    r"\bmultiple( unrelated)? families",
    r"\bserves? (over |more than )?\d+\+? (client )?families",
    r"\bclients? (include|are) (multiple |several |various )?(wealthy |ultra-high-net-worth )?families",
    r"~?\d+\+? (client|family) relationships",
    r"\bplatform (serving|for) (multiple|several|various) families",
    r"\bclient families",
    r"\bfamilies we serve",
    r"\bour client families",
    # Mined from real UTD-pool text 2026-07-26 (Compound, Pulliam, Alpha Capital, etc.) — real
    # MFOs describe themselves this way far more often than with the formal "multi-family
    # office" term itself.
    r"\bserving?[\w\s,-]{0,40} families\b",
    r"\bwork(s|ing)? with (approximately |about )?\d+\+? families\b",
    r"\bwe serve:? [\w\s,-]{0,60}families\b",
    r"\bour families\b",
    r"\bfamilies (spanning|across) multiple generations\b",
    r"\blimited number of families\b",
]


@dataclass
class ClassificationResult:
    classification: Classification
    evidence_span: str | None
    evidence: str | None  # human-readable explanation, not just the raw span


# Firm-anchor requirement (2026-07-26, replaces the earlier denylist approach). The denylist
# (reject a match near "prior to founding", "formerly at", etc.) caught the Arrowroot failure
# but is an open-ended list of ways a match can belong to someone else — it only ever grows as
# new failure shapes turn up (the Destiny finding, a blog-headline quote, was already a shape
# the denylist didn't cover). A positive requirement is more robust: a marker phrase only
# counts if the surrounding text actually anchors it to THIS firm, either a first-person voice
# ("we are", "we serve", "our firm") or the firm's own name nearby. Third-party bios, quoted
# article headlines, and generic industry framing don't carry either anchor and are rejected
# by omission rather than by an ever-growing list of what they look like.
FIRST_PERSON_ANCHORS: list[str] = [
    r"\bwe are\b",
    r"\bwe serve\b",
    r"\bour firm\b",
    r"\bour clients?\b",
    r"\bour practice\b",
    r"\bwe provide\b",
    r"\bwe offer\b",
    r"\bwe help\b",
    r"\bwe work with\b",
    r"\bwe build\b",
    r"\bour team\b",
    r"\bour approach\b",
]
_ANCHOR_WINDOW = 100  # chars to look on each side of the match

# Generic suffix words stripped from a firm's legal name before using it as a name-anchor —
# "Family Office LLC" is shared by dozens of unrelated firms and would anchor to anyone's text.
_NAME_SUFFIX_STOPWORDS = {
    "family", "office", "offices", "llc", "inc", "corp", "corporation", "company", "co",
    "partners", "group", "advisors", "advisor", "wealth", "management", "capital", "the", "of",
    "and", "llp", "ltd",
}


def _name_anchor_tokens(firm_name: str | None) -> list[str]:
    if not firm_name:
        return []
    words = re.findall(r"[a-z0-9]+", firm_name.lower())
    return [w for w in words if len(w) >= 3 and w not in _NAME_SUFFIX_STOPWORDS]


# A raw "firm name appears somewhere in the window" check is not enough by itself: verified
# against the actual Arrowroot page text, "Arrowroot Family Office, LLC" sits only 88 characters
# before the false "multi-family office" match (in "...founding Arrowroot Family Office, LLC,
# he was a Director for Salem Partners Wealth Management, a multi-family office...") — well
# inside a 100-char window, so name-proximity alone still accepts it. The missing piece: a
# DIFFERENT capitalized multi-word organization name (here, "Salem Partners Wealth Management")
# sits between the firm's own name and the marker phrase — that's the actual signal that the
# subject changed mid-window. Two or more consecutive capitalized words not belonging to the
# firm's own name, appearing between the name-anchor and the match, invalidates the anchor.
_CAPITALIZED_PHRASE_RE = re.compile(r"(?:[A-Z][a-zA-Z&.'’]*\s+){1,5}[A-Z][a-zA-Z&.'’]*")


def _has_competing_entity_between(raw_text: str, anchor_end: int, match_start: int, name_tokens: list[str]) -> bool:
    if anchor_end >= match_start:
        return False
    between = raw_text[anchor_end:match_start]
    for phrase in _CAPITALIZED_PHRASE_RE.findall(between):
        phrase_tokens = re.findall(r"[a-z0-9]+", phrase.lower())
        if any(t in name_tokens for t in phrase_tokens):
            continue  # phrase overlaps the firm's own name — not a competing entity
        if len(phrase_tokens) >= 2:
            return True
    return False


def _has_anchor(raw_text: str, start: int, end: int, name_tokens: list[str]) -> bool:
    lower = raw_text.lower()
    window_start = max(0, start - _ANCHOR_WINDOW)
    window_end = min(len(raw_text), end + _ANCHOR_WINDOW)
    window = lower[window_start:window_end]
    if any(re.search(p, window) for p in FIRST_PERSON_ANCHORS):
        return True
    for tok in name_tokens:
        for m in re.finditer(rf"\b{re.escape(tok)}\b", window):
            abs_pos = window_start + m.end()
            if abs_pos <= start and _has_competing_entity_between(raw_text, abs_pos, start, name_tokens):
                continue  # a different organization intervenes — not a valid anchor
            return True
    return False


# Bio-transition guard (2026-07-26, reinstated after the TriEdge false positive). This was
# originally the "third-party-reference" denylist, removed when the firm-anchor requirement was
# introduced on the assumption the anchor rule was a strict superset — it wasn't. TriEdge's own
# name legitimately sat inside the anchor window of "Prior to joining TriEdge, Keren spent three
# years at a multi-family office, where she managed the firm's administrative..." — the anchor
# passed, but the sentence describes an EMPLOYEE'S PRIOR EMPLOYER, an unnamed company, not
# TriEdge. The existing competing-entity check (above) only catches a NAMED multi-word
# organization intervening between the anchor and the match; it can't catch a transition into an
# unnamed prior employer, which has no name to detect at all. That's a different failure shape,
# not a redundant one — both checks now run, and either can reject a match on its own.
_BIO_TRANSITION_PATTERNS: list[str] = [
    r"\bprior to joining\b",
    r"\bbefore joining\b",
    r"\bprior to founding\b",
    r"\bbefore founding\b",
    r"\bformerly at\b",
    r"\bformerly with\b",
    r"\bpreviously at\b",
    r"\bpreviously with\b",
    r"\bspent\s+\w+\s+years?\s+at\b",
    r"\bearlier in her career\b",
    r"\bearlier in his career\b",
    r"\bbegan her career\b",
    r"\bbegan his career\b",
    r"\bafter leaving\b",
    r"\bleft to join\b",
]
_BIO_TRANSITION_WINDOW = 150  # chars to look back from the match start


def _preceded_by_bio_transition(lower_text: str, match_start: int) -> bool:
    window = lower_text[max(0, match_start - _BIO_TRANSITION_WINDOW):match_start]
    return any(re.search(p, window) for p in _BIO_TRANSITION_PATTERNS)


def _find_marker(text: str, patterns: list[str], name_tokens: list[str]) -> re.Match | None:
    """Returns the first marker match that carries a firm anchor within reach AND isn't
    preceded by a bio-transition phrase — both checks must pass independently. Scans all
    matches for a pattern (and all patterns) rather than stopping at the first hit, since a
    firm's own self-description is not guaranteed to be the first occurrence of a marker
    phrase in the page (a blog headline or a bio aside can easily come first)."""
    lower = text.lower()
    for pattern in patterns:
        for m in re.finditer(pattern, lower):
            if _preceded_by_bio_transition(lower, m.start()):
                continue
            if _has_anchor(text, m.start(), m.end(), name_tokens):
                return m
    return None


def classify(text: str, firm_name: str | None = None) -> ClassificationResult:
    """text should be the pool of source text available for this firm — press description,
    first-party site copy, classification-relevant snippets — NOT the firm name used alone as
    classification input. Classifying from the name alone is exactly the mistake this module
    exists to prevent; firm_name is used only to anchor an already-found marker phrase to this
    specific entity, never to manufacture a match by itself."""
    if not text:
        return ClassificationResult(Classification.UNKNOWN, None,
                                     "No source text available to classify from.")

    name_tokens = _name_anchor_tokens(firm_name)
    sfo_match = _find_marker(text, SFO_MARKERS, name_tokens)
    mfo_match = _find_marker(text, MFO_MARKERS, name_tokens)

    if sfo_match and mfo_match:
        # Both markers present — e.g. a firm that started as an SFO and now takes outside
        # capital (the Point72 pattern from the earlier pilot). Do not silently pick one.
        return ClassificationResult(
            Classification.UNKNOWN,
            text[sfo_match.start():sfo_match.end()] + " | " + text[mfo_match.start():mfo_match.end()],
            "Both single-family and multi-family language found — conflicting evidence, "
            "needs a human judgment call, not an automatic pick.",
        )
    if sfo_match:
        span = text[max(0, sfo_match.start() - 40):sfo_match.end() + 40].strip()
        return ClassificationResult(Classification.SFO, span,
                                     f"Affirmative single-family language found: {span!r}")
    if mfo_match:
        span = text[max(0, mfo_match.start() - 40):mfo_match.end() + 40].strip()
        return ClassificationResult(Classification.MFO, span,
                                     f"Affirmative multi-family language found: {span!r}")

    return ClassificationResult(
        Classification.UNKNOWN, None,
        "No affirmative single- or multi-family language found in available source text. "
        "A family surname in the entity's own name is not, by itself, evidence of SFO status.",
    )
