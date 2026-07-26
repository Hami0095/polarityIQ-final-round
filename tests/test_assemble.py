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
        firm_email=SourcedField(
            value=email, confidence=Confidence.HIGH,
            evidence_span=f"Contact us: {email}",
        ) if email else SourcedField(),
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


def test_evidence_span_gate_rejects_unsupported_value():
    """The Real Capital Solutions incident, as a regression test: a value with
    no evidence_span (or an evidence_span that doesn't literally contain it)
    must be nulled, exactly like a WebFetch-summary-invented email would be."""
    firm = Firm(
        firm_id="x", name="x", classification=Classification.SFO, discovery_source="Press",
        firm_email=SourcedField(value="fake@example.com", confidence=Confidence.HIGH,
                                 evidence_span="Contact us at the office."),  # doesn't contain the value
    )
    audit_log, inconclusive_log = [], []
    validate_and_null(firm, audit_log, inconclusive_log)
    assert firm.firm_email.value is None
    assert any("evidence check" in row["reason"] for row in audit_log)


def test_domain_level_cap_catches_channel_label_laundering():
    """Two records labeled with different discovery_source strings but both
    pointing at the same listicle domain must still trip the cap — the exact
    failure mode that let billionaire-listicle records read as diversified."""
    from dataset.assemble import enforce_source_cap, SourceConcentrationError
    firms = [
        Firm(firm_id="a", name="a", discovery_source="Regional/Sector Directory",
             discovery_url="https://familyofficehub.io/a"),
        Firm(firm_id="b", name="b", discovery_source="Billionaire List",
             discovery_url="https://familyofficehub.io/b"),
        Firm(firm_id="c", name="c", discovery_source="Press", discovery_url="https://axios.com/c"),
        Firm(firm_id="d", name="d", discovery_source="990", discovery_url="https://propublica.org/d"),
    ]
    try:
        enforce_source_cap(firms, cap=0.35)
        assert False, "expected SourceConcentrationError from domain-level check"
    except SourceConcentrationError:
        pass
