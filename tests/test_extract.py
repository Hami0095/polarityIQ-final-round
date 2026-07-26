"""Regression test for the minimax-m3:cloud fabrication caught 2026-07-25 (see DECISIONS.md):
a model can fabricate a value AND a plausible-looking evidence_span for it together. Checking
only "is value inside evidence_span" is not enough — evidence_span itself must be verified as a
real substring of the fetched document. No network/model call here; this tests the parsing
logic in extract_with_llm() directly against a fixed fake model response.
"""
from __future__ import annotations

import json
from unittest.mock import patch

from enrichment.extract import extract_with_llm

SOURCE_TEXT = "Mactaggart Family & Partners. 2 Babmaes Street, London. T: +44 (0)20 7491 2948."


def _fake_response(payload: dict) -> str:
    return json.dumps(payload)


def test_fabricated_value_with_fabricated_span_is_rejected():
    fake = {
        "aum": {"value": "$1.2B", "evidence_span": "assets under management of $1.2B"},  # not in source
        "hq_city": {"value": "London", "evidence_span": "2 Babmaes Street, London"},  # real
    }
    with patch("enrichment.extract._ollama_chat", return_value=_fake_response(fake)):
        fields = extract_with_llm(SOURCE_TEXT, "https://example.com", "2026-07-25T00:00:00Z")

    assert fields["aum"].value is None, "fabricated value+span pair must be rejected"
    assert fields["hq_city"].value == "London", "a genuinely supported value must survive"


def test_value_not_contained_in_its_own_span_is_rejected():
    fake = {"hq_city": {"value": "Paris", "evidence_span": "2 Babmaes Street, London"}}
    with patch("enrichment.extract._ollama_chat", return_value=_fake_response(fake)):
        fields = extract_with_llm(SOURCE_TEXT, "https://example.com", "2026-07-25T00:00:00Z")
    assert fields["hq_city"].value is None
