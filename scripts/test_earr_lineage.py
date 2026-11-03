"""Negative and positive acceptance fixtures for the EARR amendment proposal.

These verify only the *reference decision model*, not source authenticity or
the authoritative Richard/EARR schema. Run: python3 scripts/test_earr_lineage.py
"""
import unittest

from earr_lineage import ReviewClass, ReviewLineage, classify_lineage


def case(
    claimant_agent="ci-runner",
    claimant_principal="repo-owner",
    preparer_agent="gpt-6-assistant",
    preparer_principal="repo-owner",
    independent_appointment=None,
    direct_primary_source_read=None,
    separately_controlled_evidence_custody=None,
    conflicts_assessed=None,
    unfiltered_access=None,
):
    return ReviewLineage(
        claimant_agent, claimant_principal, preparer_agent,
        preparer_principal, independent_appointment,
        direct_primary_source_read, separately_controlled_evidence_custody,
        conflicts_assessed, unfiltered_access,
    )


class EARRLineageProvisionalTests(unittest.TestCase):
    def assert_class(self, given, expected):
        result = classify_lineage(given)
        self.assertEqual(result.review_class, expected)
        self.assertFalse(result.independent_witness_qualified)
        self.assertTrue(result.reason)

    def test_fixture_a_same_agent_same_principal(self):
        self.assert_class(
            case(preparer_agent="ci-runner"),
            ReviewClass.SELF_REVIEW,
        )

    def test_fixture_b_run75_other_agent_same_principal(self):
        self.assert_class(case(), ReviewClass.DELEGATED_NON_INDEPENDENT)

    def test_fixture_c_different_principal_but_copies_owner_verdict(self):
        self.assert_class(
            case(preparer_principal="unaffiliated-reviewer",
                 independent_appointment=True,
                 direct_primary_source_read=False,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.UNVERIFIED,
        )

    def test_fixture_d_conditions_satisfied_only_eligible(self):
        self.assert_class(
            case(preparer_principal="unaffiliated-reviewer",
                 independent_appointment=True, direct_primary_source_read=True,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.ELIGIBLE_FOR_INDEPENDENT_ASSESSMENT,
        )

    def test_fixture_e_unknown_principal_never_promoted(self):
        self.assert_class(
            case(preparer_principal=None),
            ReviewClass.UNVERIFIED,
        )

    def test_same_agent_different_claimed_principal_is_self_review(self):
        self.assert_class(
            case(preparer_agent="ci-runner",
                 preparer_principal="unaffiliated-reviewer"),
            ReviewClass.SELF_REVIEW,
        )

    def test_same_principal_cannot_be_promoted_by_claimed_good_custody(self):
        self.assert_class(
            case(independent_appointment=True, direct_primary_source_read=True,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.DELEGATED_NON_INDEPENDENT,
        )

    def test_missing_custody_blocks_eligibility(self):
        self.assert_class(
            case(preparer_principal="unaffiliated-reviewer",
                 independent_appointment=True, direct_primary_source_read=True,
                 separately_controlled_evidence_custody=None,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.UNVERIFIED,
        )

    def test_undisclosed_conflicts_block_eligibility(self):
        self.assert_class(
            case(preparer_principal="unaffiliated-reviewer",
                 independent_appointment=True, direct_primary_source_read=True,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=False, unfiltered_access=True),
            ReviewClass.UNVERIFIED,
        )

    def test_principal_whitespace_alias_cannot_fake_separation(self):
        self.assert_class(
            case(preparer_principal="repo-owner ", independent_appointment=True,
                 direct_primary_source_read=True,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.DELEGATED_NON_INDEPENDENT,
        )

    def test_agent_case_alias_cannot_fake_separation(self):
        self.assert_class(
            case(preparer_agent="CI-RUNNER", preparer_principal="outside",
                 independent_appointment=True, direct_primary_source_read=True,
                 separately_controlled_evidence_custody=True,
                 conflicts_assessed=True, unfiltered_access=True),
            ReviewClass.SELF_REVIEW,
        )


if __name__ == "__main__":
    unittest.main()
