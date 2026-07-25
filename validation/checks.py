"""Real, running verification checks — not just prompted "looks good" judgments.

Each function returns (passed: bool, detail: str) so results can be logged
per-record. Failed checks are enforced by callers: the failing cell gets
nulled in the delivered dataset, and the raw attempt is preserved in the
audit/rejected log, per PROJECT_BRIEF.md's honesty rules.
"""
from __future__ import annotations

import re
import time

import dns.resolver
import phonenumbers

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

_mx_cache: dict[str, tuple[bool, str]] = {}


class MXCheckInconclusive(Exception):
    """Raised when MX lookup couldn't get a definitive answer (network
    timeout, resolver error) after retries — this is NOT the same as
    NXDOMAIN/NoAnswer, which are definitive negatives. Treating a timeout
    as "undeliverable" would wrongly null out a possibly-valid address, so
    callers must not silently swallow this into a pass/fail."""


def _resolve_mx(domain: str, retries: int = 3, delay: float = 1.5) -> tuple[bool, str]:
    if domain in _mx_cache:
        return _mx_cache[domain]

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            dns.resolver.resolve(domain, "MX")
            result = (True, "MX record found")
            _mx_cache[domain] = result
            return result
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            # definitive: domain doesn't exist or genuinely has no MX record
            result = (False, f"no MX record ({type(e).__name__}) — domain cannot receive mail")
            _mx_cache[domain] = result
            return result
        except Exception as e:  # timeout, resolver/network error — not definitive
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)

    raise MXCheckInconclusive(
        f"MX lookup for {domain} did not get a definitive answer after {retries} attempts "
        f"(last error: {type(last_err).__name__}: {last_err}) — this is a network/resolver "
        f"issue, not evidence the address is undeliverable."
    )


def check_email(email: str) -> tuple[bool, str]:
    if not EMAIL_RE.match(email):
        return False, "failed syntax check"

    domain = email.split("@", 1)[1]
    has_mx, detail = _resolve_mx(domain)  # raises MXCheckInconclusive if genuinely unresolvable

    if not has_mx:
        return False, f"syntax OK but {detail} (undeliverable)"
    return True, f"syntax OK, {detail}"


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
