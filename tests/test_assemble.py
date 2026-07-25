from dataset.schema import Classification, Confidence, Firm, Principal, SourcedField
from dataset.assemble import (
    SourceConcentrationError,
    enforce_source_cap,
    validate_and_null,
)


def _firm(firm_id, discovery_source, email=None):
    return Firm(
        firm_id=firm_id,
        name=firm_id,
        classification=Classification.SFO,
        discovery_source=discovery_source,
        firm_email=SourcedField(value=email, confidence=Confidence.HIGH) if email else SourcedField(),
    )


def test_source_cap_raises_when_exceeded():
    firms = [_firm("a", "EDGAR"), _firm("b", "EDGAR"), _firm("c", "EDGAR"), _firm("d", "Press")]
    try:
        enforce_source_cap(firms, cap=0.35)
        assert False, "expected SourceConcentrationError"
    except SourceConcentrationError:
        pass


def test_source_cap_passes_when_diversified():
    firms = [_firm("a", "EDGAR"), _firm("b", "Press"), _firm("c", "990"), _firm("d", "Conference")]
    enforce_source_cap(firms, cap=0.35)  # should not raise


def test_validate_and_null_rejects_bad_email():
    firm = _firm("x", "Press", email="someone@this-domain-should-not-exist-zzz123.com")
    audit_log, inconclusive_log = [], []
    validate_and_null(firm, audit_log, inconclusive_log)
    assert firm.firm_email.value is None
    assert len(audit_log) == 1


def test_validate_and_null_keeps_good_email():
    firm = _firm("x", "Press", email="info@p1fo.com")
    audit_log, inconclusive_log = [], []
    validate_and_null(firm, audit_log, inconclusive_log)
    assert firm.firm_email.value == "info@p1fo.com"
    assert len(audit_log) == 0
