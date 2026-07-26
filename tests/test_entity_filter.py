from dataset.entity_filter import check_entity_type


def test_fund_vehicle_with_family_office_words_still_rejected():
    """The core finding from the EDGAR viability check: 'family office' words in a name do
    not exempt a fund vehicle from rejection."""
    r = check_entity_type("Wilshire Private Markets Family Office Fund II, L.P.")
    assert r.rejected
    assert "fund" in r.evidence_span.lower()


def test_bare_fund_word_rejected_without_numeral():
    r = check_entity_type("PAVP Family Office Fund, LP")
    assert r.rejected


def test_operating_family_office_name_passes():
    for name in ["White Knight Family Office LLC", "Virtus Family Office LLC",
                 "PointOne Family Office, LLC", "Danis Family Office, LLC"]:
        assert not check_entity_type(name).rejected, name


def test_trust_company_rejected_when_not_self_described_as_family_office():
    r = check_entity_type("First National Trust Company")
    assert r.rejected


def test_family_office_and_trust_not_rejected_for_trust_word_alone():
    """'Lexington Family Office & Trust, LLC' should not be rejected just because it
    contains 'Trust' — the family-office self-marker exempts it from the institutional
    trust-company pattern."""
    r = check_entity_type("Lexington Family Office & Trust, LLC")
    assert not r.rejected


def test_law_firm_rejected():
    r = check_entity_type("Smith & Jones LLP")
    assert r.rejected


def test_spv_series_rejected():
    r = check_entity_type("Betty Labs SPV, a series of Lambeth Family Office LLC")
    assert r.rejected
