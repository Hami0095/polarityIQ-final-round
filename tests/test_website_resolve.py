"""Regression test for the pointone.com false positive caught 2026-07-25 (see DECISIONS.md):
a domain guess for "PointOne Family Office, LLC" landed on an unrelated AI billing startup
that happens to share the brand word "PointOne". No network calls here — tests
_page_matches_firm() directly against fixed fake page content.
"""
from __future__ import annotations

from enrichment.website_resolve import _page_matches_firm

POINTONE_FAKE_PAGE = (
    "<title>PointOne</title>"
    "<meta name='description' content='PointOne uses AI to passively track time and review "
    "bills. Capture detailed time data that drives insights across your practice.'>"
)

REAL_FAMILY_OFFICE_PAGE = (
    "<title>PointOne Family Office</title>"
    "<meta name='description' content='PointOne Family Office is a single-family office "
    "providing wealth management and investment services to one family.'>"
)


def test_brand_word_collision_is_rejected():
    assert _page_matches_firm("PointOne Family Office, LLC", POINTONE_FAKE_PAGE) is False


def test_real_family_office_page_is_accepted():
    assert _page_matches_firm("PointOne Family Office, LLC", REAL_FAMILY_OFFICE_PAGE) is True
