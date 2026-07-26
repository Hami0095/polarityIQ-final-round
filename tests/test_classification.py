from dataset.schema import Classification
from dataset.classification import classify


def test_surname_alone_does_not_imply_sfo():
    """The explicit non-goal: a family surname in the name is not evidence. This function only
    ever sees body text, but as a sanity check, body text that's JUST the name should not
    classify as SFO."""
    result = classify("Danis Family Office, LLC")
    assert result.classification == Classification.UNKNOWN


def test_affirmative_sfo_language_classifies_as_sfo():
    text = "Mactaggart Family & Partners is a single-family office managing the Mactaggart family's own wealth."
    result = classify(text, firm_name="Mactaggart Family & Partners")
    assert result.classification == Classification.SFO
    assert result.evidence_span and "single-family office" in result.evidence_span.lower()


def test_affirmative_mfo_language_classifies_as_mfo():
    text = "Pathstone is a multi-family office serving over 500 client families across the country."
    result = classify(text, firm_name="Pathstone")
    assert result.classification == Classification.MFO
    assert result.evidence_span


def test_marker_without_firm_anchor_is_rejected():
    """A marker phrase describing a THIRD PARTY (no first-person voice, no subject-firm name
    nearby) must not classify — this is the Arrowroot/Destiny failure shape: the anchor
    requirement rejects it by omission rather than by matching a denylist pattern."""
    text = (
        "Prior to founding Ridgeline Advisors, he was a Director for Salem Partners Wealth "
        "Management, a multi-family office and investment bank in Los Angeles."
    )
    result = classify(text, firm_name="Ridgeline Advisors")
    assert result.classification == Classification.UNKNOWN


def test_bio_transition_guard_rejects_prior_employer_even_with_valid_anchor():
    """The TriEdge false positive: the firm's own name sits legitimately inside the anchor
    window, but the sentence describes an employee's PRIOR employer, not the firm itself. The
    anchor rule alone accepts this (the name really is nearby); the bio-transition guard is a
    second, independent check that catches what the anchor rule structurally cannot — an
    unnamed prior employer has no competing entity name for the anchor rule's own
    competing-entity check to detect."""
    text = (
        "...at TriEdge Investments, where she oversees the firm's day-to-day office operations. "
        "Prior to joining TriEdge, Keren spent three years at a multi-family office, where she "
        "managed the firm's administrative and operational functions."
    )
    result = classify(text, firm_name="TriEdge Investments")
    assert result.classification == Classification.UNKNOWN


def test_quoted_article_headline_is_rejected():
    """A blog headline about the industry ('The Rise of Multi Family Offices...') carries
    neither a first-person anchor nor the firm's own name and must not classify."""
    text = "Read More -> Wealth of Ideas -> The Rise of Multi Family Offices: Independence, Complexity, and Sophistication"
    result = classify(text, firm_name="Destiny Family Office")
    assert result.classification == Classification.UNKNOWN


def test_no_evidence_is_unable_to_determine():
    text = "A boutique investment firm headquartered in Chicago specializing in real estate."
    result = classify(text)
    assert result.classification == Classification.UNKNOWN


def test_conflicting_evidence_stays_unable_to_determine():
    text = "We are a single-family office by history, and we now serve multiple unrelated families as clients."
    result = classify(text, firm_name="Example Capital")
    assert result.classification == Classification.UNKNOWN
    assert "conflicting" in result.evidence.lower()


def test_empty_text_is_unable_to_determine():
    result = classify("")
    assert result.classification == Classification.UNKNOWN


def test_ceo_bio_self_reference_survives_both_guards():
    """Element Pointe's real evidence: a CEO bio that names the firm and describes the firm
    itself (not a prior employer). Must still classify — the bio-transition guard must not
    over-reject genuine self-description just because it appears in bio-shaped text."""
    text = (
        "David Savir is Co-Founder and Chief Executive Officer of Element Pointe Family "
        "Office, a multi-family office and investment advisory firm serving high-net-worth "
        "families and family offices throughout the U.S."
    )
    result = classify(text, firm_name="Element Pointe Family Office")
    assert result.classification == Classification.MFO


def test_homepage_self_description_survives_both_guards():
    """Mayfair's real evidence: a direct, present-tense homepage self-description naming the
    firm. Must still classify."""
    text = "MAYFAIR Vermogensverwaltungs SE - Single Family Office mit ueber 20 Jahren Erfahrung. Wir sind ein familiengefuehrtes Unternehmen."
    result = classify(text, firm_name="Mayfair Vermogensverwaltungs")
    assert result.classification == Classification.SFO
