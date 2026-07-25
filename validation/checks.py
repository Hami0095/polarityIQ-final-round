"""Real, running verification checks — not just prompted "looks good" judgments.

Each function returns (passed: bool, detail: str) so results can be logged
per-record. Failed checks are enforced by callers: the failing cell gets
nulled in the delivered dataset, and the raw attempt is preserved in the
audit/rejected log, per PROJECT_BRIEF.md's honesty rules.
"""
from __future__ import annotations

import re

import dns.resolver
import phonenumbers

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

_mx_cache: dict[str, bool] = {}


def check_email(email: str) -> tuple[bool, str]:
    if not EMAIL_RE.match(email):
        return False, "failed syntax check"

    domain = email.split("@", 1)[1]
    if domain in _mx_cache:
        has_mx = _mx_cache[domain]
    else:
        try:
            dns.resolver.resolve(domain, "MX")
            has_mx = True
        except Exception as e:  # NXDOMAIN, NoAnswer, Timeout, etc.
            has_mx = False
        _mx_cache[domain] = has_mx

    if not has_mx:
        return False, "syntax OK but domain has no MX record (undeliverable)"
    return True, "syntax OK, domain has valid MX record"


def check_phone(number: str, region: str = "US") -> tuple[bool, str]:
    try:
        parsed = phonenumbers.parse(number, region)
    except phonenumbers.NumberParseException as e:
        return False, f"failed to parse: {e}"

    if not phonenumbers.is_valid_number(parsed):
        return False, "parsed but not a valid number for its region"

    formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return True, f"valid, region-checked, normalized to {formatted}"


def corroboration_ok(source_urls: list[str], min_sources: int = 2) -> tuple[bool, str]:
    """AUM/thesis-type claims need corroboration from >=2 independent sources
    (or 1 if it's a primary regulatory filing like SEC ADV/EDGAR)."""
    unique_domains = {u.split("/")[2] for u in source_urls if "://" in u}
    if len(unique_domains) >= min_sources:
        return True, f"corroborated across {len(unique_domains)} independent domains"
    if len(unique_domains) == 1 and any(
        d.endswith(("sec.gov", "propublica.org")) for d in unique_domains
    ):
        return True, "single source but a primary regulatory/public-filing source"
    return False, f"only {len(unique_domains)} independent source(s), below corroboration bar"
