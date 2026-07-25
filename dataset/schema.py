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
    NAMED_DIRECT = "Named principal + direct contact"
    NAMED_FIRM_LEVEL = "Named principal + firm-level contact"
    NAMED_NO_CONTACT = "Named principal, no contact"
    FIRM_LEVEL_ONLY = "Firm-level contact only"
    NONE = "No reachable contact"


class SourcedField(BaseModel):
    """A single value plus how we know it."""
    value: Optional[str] = None
    source_url: Optional[str] = None
    verification_method: Optional[str] = None
    confidence: Confidence = Confidence.NONE
    checked_at: Optional[str] = None  # ISO date the source/check was last run

    @property
    def is_verified(self) -> bool:
        return self.value is not None and self.confidence in (
            Confidence.HIGH,
            Confidence.MEDIUM,
        )


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

    discovery_source: str
    discovery_url: Optional[str] = None

    principals: list[Principal] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)

    blind_spots: Optional[str] = None
    rejected_reason: Optional[str] = None  # set if filtered out before final 50

    def contact_actionability(self) -> ContactActionability:
        """Computed from delivered (post-validation) cells only, so it can
        never claim more than what's actually in the file."""
        has_named_principal = any(p.full_name for p in self.principals)
        has_principal_contact = any(
            p.work_email.value or p.direct_phone.value for p in self.principals
        )
        has_firm_contact = bool(self.firm_email.value or self.firm_phone.value)

        if has_named_principal and has_principal_contact:
            return ContactActionability.NAMED_DIRECT
        if has_named_principal and has_firm_contact:
            return ContactActionability.NAMED_FIRM_LEVEL
        if has_named_principal:
            return ContactActionability.NAMED_NO_CONTACT
        if has_firm_contact:
            return ContactActionability.FIRM_LEVEL_ONLY
        return ContactActionability.NONE
