from discovery.websearch import _classify_url


def test_directory_domain_classified_as_directory():
    assert _classify_url("https://familyofficehub.io/profile/x", "x") == "directory"
    assert _classify_url("https://www.linkedin.com/company/x", "x") == "directory"


def test_press_domain_classified_as_press():
    assert _classify_url("https://www.businesswire.com/news/x", "x") == "press"


def test_aggregator_domain_classified_as_directory_not_first_party():
    """Confirmed false-positive-shaped cases from 2026-07-25 (DECISIONS.md): 13F/EIN/ADV
    aggregators legitimately contain a firm's name but are not its own site."""
    assert _classify_url("https://aum13f.com/firm/danis-family-office-llc", "danis") == "directory"
    assert _classify_url("https://eintaxid.com/company/x-danis-family-office", "danis") == "directory"


def test_slug_matching_domain_classified_first_party():
    assert _classify_url("https://mactaggartfp.com/", "mactaggart") == "first_party"
