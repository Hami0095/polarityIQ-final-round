"""Shared data model for firm/principal/signal records.

Every high-value field is paired with a source and a confidence level so
enrichment and validation can be traced cell-by-cell, per PROJECT_BRIEF.md's
proof rules. Fields that cannot be verified stay None and get labeled
"could not verify" rather than guessed.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = "Could not verify"


class Classification(str, Enum):
    SFO = "Single-Family Office"
    MFO = "Multi-Family Office"
    UNKNOWN = "Unable to Determine"


class ContactActionability(str, Enum):
    """How usable a record's contact info is today. Computed from what
    actually made it through validation, not authored by hand, so it can't
    drift from the delivered cells."""
    NAMED_DIRECT = "Named principal + direct contact for that principal"
    NAMED_OTHER_DIRECT = "Named principal(s); direct contact reaches a different named person at the firm, not the listed principal"
    NAMED_FIRM_LEVEL = "Named principal + firm-level contact"
    NAMED_NO_CONTACT = "Named principal, no contact"
    FIRM_LEVEL_ONLY = "Firm-level contact only"
    NONE = "No reachable contact"


class SourcedField(BaseModel):
    """A single value plus how we know it.

    evidence_span/fetched_at/source_doc_len exist because of a real incident
    (2026-07-25, Real Capital Solutions team page): a WebFetch summary
    reported plausible emails that did not exist in the page's raw HTML
    (Cloudflare-obfuscated addresses the summarizer filled in with a
    plausible guess). Requiring the literal source snippet at extraction
    time, and rejecting any field whose value isn't a substring match of its
    own evidence_span, makes that failure mode structurally impossible
    instead of relying on remembering to check by hand next time.
    """
    value: Optional[str] = None
    source_url: Optional[str] = None
    verification_method: Optional[str] = None
    confidence: Confidence = Confidence.NONE
    checked_at: Optional[str] = None  # ISO date the source/check was last run
    evidence_span: Optional[str] = None  # literal snippet of fetched text the value was drawn from
    fetched_at: Optional[str] = None  # ISO timestamp the source document was fetched
    source_doc_len: Optional[int] = None  # len() of the fetched document, for provenance/debugging

    @property
    def is_verified(self) -> bool:
        return self.value is not None and self.confidence in (
            Confidence.HIGH,
            Confidence.MEDIUM,
        )

    def evidence_supports_value(self) -> bool:
        """A field with no value has nothing to support. A field with a value
        but no evidence_span, or whose value isn't actually present in its own
        evidence_span, fails — this is the anti-fabrication gate."""
        if self.value is None:
            return True
        if not self.evidence_span:
            return False
        return self.value.strip().lower() in self.evidence_span.strip().lower()


class DiscoveryRecord(BaseModel):
    """Output of the discovery layer: one candidate firm, pre-enrichment."""
    candidate_id: str
    name_as_found: str
    discovery_source: str  # e.g. "SEC ADV", "ProPublica 990", "press:Bloomberg", "conference:..."
    discovery_url: Optional[str] = None
    discovery_query: Optional[str] = None
    discovered_at: Optional[str] = None
    domain_guess: Optional[str] = None
    notes: Optional[str] = None


class Signal(BaseModel):
    signal_type: str  # investment | fund_commitment | hire | news
    description: str
    signal_date: Optional[str] = None
    source_url: str
    confidence: Confidence = Confidence.MEDIUM


class Principal(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: SourcedField = Field(default_factory=SourcedField)
    work_email: SourcedField = Field(default_factory=SourcedField)
    direct_phone: SourcedField = Field(default_factory=SourcedField)


class Firm(BaseModel):
    firm_id: str
    name: str
    description: SourcedField = Field(default_factory=SourcedField)
    investment_thesis: SourcedField = Field(default_factory=SourcedField)
    sectors: SourcedField = Field(default_factory=SourcedField)
    aum: SourcedField = Field(default_factory=SourcedField)
    hq_address: Optional[str] = None
    hq_city: Optional[str] = None
    hq_state: Optional[str] = None
    hq_country: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    corporate_linkedin: Optional[str] = None
    firm_email: SourcedField = Field(default_factory=SourcedField)  # general office contact, not attributed to an individual
    firm_phone: SourcedField = Field(default_factory=SourcedField)

    classification: Classification = Classification.UNKNOWN
    classification_evidence: Optional[str] = None
    classification_source_url: Optional[str] = None
    # Evidence-class ranking (2026-07-26): a record qualifies on AFFIRMATIVE EVIDENCE that the
    # firm is a family office at all, which is not the same question as SFO-vs-MFO subtype.
    # A: structured third-party classification (e.g. Wikidata instance/subclass-of claim).
    # B: third-party published description (news, search snippet, directory prose).
    # C: regulatory client-structure corroboration. The firm's filed legal name asserts
    #    family-office status, and its Form ADV Item 5.D client composition (high-net-worth
    #    individuals only, no institutional client categories, client count within the stated
    #    ceiling) is consistent with that assertion. This is corroborating rather than
    #    independent evidence — a boutique RIA with the same client shape but no family-office
    #    name would pass the same structural test — and is the weakest evidence class in this
    #    dataset. Records resting solely on Class C are labelled as such (see
    #    adv_item5d.py for the full inclusion-rule rationale).
    # D: first-party website self-description (the only class the pipeline used before this).
    # A firm can have evidence_class set (qualifies as "is a family office") while
    # classification stays Unable to Determine (SFO/MFO subtype genuinely not determinable) —
    # those are different questions and this project does not guess the second to answer the
    # first. See dataset/classification.py and qualifying() in enrichment/pipeline.py.
    evidence_class: Optional[str] = None
    evidence_class_detail: Optional[str] = None

    def classification_display(self) -> str:
        """Display string for the `classification` cell. "Unable to Determine" collapses
        two different claims into one ambiguous label (2026-07-26 fix): whether this is a
        family office at all, vs. whether it's specifically single- or multi-family. A
        record only ships (see qualifying() in enrichment/pipeline.py) if EITHER
        classification is SFO/MFO OR evidence_class is set — so within delivered records,
        classification == UNKNOWN always means "confirmed family office, subtype not
        established," never "we don't know if this is a family office." That gets its own
        label so a reader can't misread it as non-qualifying."""
        if self.classification == Classification.UNKNOWN:
            return "Subtype unconfirmed" if self.evidence_class else self.classification.value
        return self.classification.value

    @property
    def family_office_confirmed(self) -> bool:
        """True iff there's affirmative evidence this is a family office at all (any of
        evidence_class A-D, or a determined SFO/MFO subtype) — the qualifying-set
        criterion itself, exposed as its own field instead of being inferred from
        `classification` alone."""
        return bool(self.evidence_class) or self.classification != Classification.UNKNOWN

    discovery_source: str
    discovery_url: Optional[str] = None
    discovery_method: Optional[str] = None  # the actual query/path that surfaced this firm, e.g. the search string or 990 query

    principals: list[Principal] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)

    blind_spots: Optional[str] = None
    rejected_reason: Optional[str] = None  # set if filtered out before final 50

    def contact_actionability(self) -> ContactActionability:
        """Computed from delivered (post-validation) cells only, so it can
        never claim more than what's actually in the file.

        NAMED_DIRECT requires the SAME principal to carry both the name and
        the direct contact — not "some named principal exists" plus
        "some principal (possibly a different one) has a direct line", which
        previously let e.g. Real Capital Solutions read as "you can reach
        the decision-maker" when the phone that validated was principal_2's
        (Judy Lawson), not principal_1's (Marcel Arsenault, the listed
        decision-maker). NAMED_OTHER_DIRECT names that gap explicitly instead
        of collapsing it into the strongest-sounding label.
        """
        has_named_principal = any(p.full_name for p in self.principals)
        principal_with_own_contact = any(
            p.full_name and (p.work_email.value or p.direct_phone.value) for p in self.principals
        )
        has_principal_contact = any(
            p.work_email.value or p.direct_phone.value for p in self.principals
        )
        has_firm_contact = bool(self.firm_email.value or self.firm_phone.value)

        if principal_with_own_contact:
            return ContactActionability.NAMED_DIRECT
        if has_named_principal and has_principal_contact:
            return ContactActionability.NAMED_OTHER_DIRECT
        if has_named_principal and has_firm_contact:
            return ContactActionability.NAMED_FIRM_LEVEL
        if has_named_principal:
            return ContactActionability.NAMED_NO_CONTACT
        if has_firm_contact:
            return ContactActionability.FIRM_LEVEL_ONLY
        return ContactActionability.NONE
