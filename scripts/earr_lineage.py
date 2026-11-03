"""Non-authoritative EARR principal-lineage decision model (proposal only).

This is a falsifiable reference model for the *proposed* 2026-11-03 EARR
amendment. It is not the official EARR v0.2 schema, an EARR adjudicator,
a signature verifier, or an independent-witness certification system.
All asserted identities and disclosures require external authentication.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewClass(str, Enum):
    SELF_REVIEW = "SELF_REVIEW"
    DELEGATED_NON_INDEPENDENT = "DELEGATED_NON_INDEPENDENT"
    UNVERIFIED = "UNVERIFIED"
    ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT = "ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT"


@dataclass(frozen=True)
class ReviewLineage:
    claimant_agent: str | None
    claimant_principal: str | None
    preparer_agent: str | None
    preparer_principal: str | None
    # Booleans are declared facts requiring verification; None means UNKNOWN.
    independent_appointment: bool | None
    direct_primary_source_read: bool | None
    separately_controlled_evidence_custody: bool | None
    conflicts_assessed: bool | None
    unfiltered_access: bool | None


@dataclass(frozen=True)
class ReviewDisposition:
    review_class: ReviewClass
    independent_witness_qualified: bool
    reason: str


def _valid_identifier(value: str | None) -> bool:
    return type(value) is str and bool(value.strip())


def classify_lineage(case: ReviewLineage) -> ReviewDisposition:
    """Return a conservative lineage classification. Never grant W1 status.

    Same-agent review and same-principal delegated review are not independent.
    A different claimed principal is necessary but never sufficient; all
    review/custody conditions must be explicitly supported. This function
    cannot authenticate principals, people, signatures, or raw evidence.
    """
    ids = (
        case.claimant_agent, case.claimant_principal,
        case.preparer_agent, case.preparer_principal,
    )
    if not all(_valid_identifier(v) for v in ids):
        return ReviewDisposition(
            ReviewClass.UNVERIFIED, False, "missing_or_unverified_identity"
        )

    if case.claimant_agent == case.preparer_agent:
        return ReviewDisposition(
            ReviewClass.SELF_REVIEW, False, "same_reviewing_agent"
        )
    if case.claimant_principal == case.preparer_principal:
        return ReviewDisposition(
            ReviewClass.DELEGATED_NON_INDEPENDENT,
            False, "different_agents_same_controlling_principal",
        )

    checks = (
        case.independent_appointment,
        case.direct_primary_source_read,
        case.separately_controlled_evidence_custody,
        case.conflicts_assessed,
        case.unfiltered_access,
    )
    if not all(v is True for v in checks):
        return ReviewDisposition(
            ReviewClass.UNVERIFIED,
            False, "different_principals_but_review_conditions_incomplete",
        )

    # Eligibility remains conditional on externally authenticated identity,
    # source custody and actual reviewer inspection; it is NOT W1.
    return ReviewDisposition(
        ReviewClass.ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT,
        False, "review_conditions_declared_not_independently_certified",
    )
