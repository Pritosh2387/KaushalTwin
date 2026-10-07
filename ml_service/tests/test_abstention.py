"""
Unit Tests — Module 7: Abstention / Evidence Sufficiency Engine
"""
import pytest
from app.algorithms.abstention import (
    check_evidence_sufficiency,
    should_abstain,
    AbstentionDecision,
)
from app.services.abstention_service import AbstentionService


class TestAbstentionAlgorithm:
    def test_check_evidence_sufficiency_ready(self):
        """Test case where evidence is sufficient for assessment."""
        competencies = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 75,
                "evidence_confidence": 0.8,
                "evidence_coverage": 0.85,
            },
            {
                "nos_id": "DEMO_NOS_005",
                "mandatory": True,
                "competency_score": 70,
                "evidence_confidence": 0.75,
                "evidence_coverage": 0.8,
            },
        ]

        evidence_records = [
            {"source": "PRACTICAL", "supports": True, "notes": "Observed safe isolation"},
            {"source": "ASSESSED", "supports": True, "notes": "Assessor validated skills"},
        ]

        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=competencies,
            evidence_records=evidence_records,
        )

        assert decision.status == "READY_FOR_ASSESSOR"
        assert decision.confidence > 0.5
        assert decision.recommended_action == "PROCEED_WITH_ASSESSOR_REVIEW"
        assert decision.next_task_id is None
        assert len(decision.reason_codes) == 0  # No issues found

    def test_check_evidence_sufficiency_abstain_mandatory_low_evidence(self):
        """Test abstention due to mandatory NOS with low evidence."""
        competencies = [
            {
                "nos_id": "DEMO_NOS_004",  # Safe isolation - mandatory
                "mandatory": True,
                "competency_score": 80,  # High competency
                "evidence_confidence": 0.3,  # Low confidence
                "evidence_coverage": 0.2,  # Low coverage
            },
        ]

        evidence_records = [
            {"source": "SELF_DECLARATION", "supports": True, "notes": "Claims 5 years experience"},
            # No practical or assessor evidence
        ]

        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=competencies,
            evidence_records=evidence_records,
        )

        assert decision.status == "ABSTAIN"
        assert decision.confidence >= 0.1
        assert "MANDATORY_EVIDENCE_MISSING" in decision.reason_codes
        assert "LOW_EVIDENCE_CONFIDENCE" in decision.reason_codes
        assert decision.recommended_action == "HUMAN_REVIEW_REQUIRED"
        assert any("Mandatory NOS" in reason for reason in decision.reasons)

    def test_check_evidence_sufficiency_needs_more_evidence(self):
        """Test case needing more evidence but not critical."""
        competencies = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 60,
                "evidence_confidence": 0.5,
                "evidence_coverage": 0.4,  # Borderline
            },
            {
                "nos_id": "DEMO_NOS_005",
                "mandatory": False,
                "competency_score": 50,
                "evidence_confidence": 0.4,
                "evidence_coverage": 0.3,
            },
        ]

        evidence_records = [
            {"source": "SELF_DECLARATION", "supports": True, "notes": "Self-declared experience"},
            # Minimal evidence
        ]

        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=competencies,
            evidence_records=evidence_records,
        )

        assert decision.status == "NEEDS_MORE_EVIDENCE"
        assert decision.recommended_action == "RUN_TARGETED_ASSESSMENT"
        assert decision.next_task_id is not None  # Should suggest a task
        assert ("LOW_OVERALL_EVIDENCE_COVERAGE" in decision.reason_codes or
                len(decision.reason_codes) > 1)  # Multiple issues

    def test_check_evidence_sufficiency_conflict_review(self):
        """Test case with significant evidence conflicts."""
        competencies = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 65,
                "evidence_confidence": 0.6,
                "evidence_coverage": 0.6,
            },
        ]

        # Mixed evidence: some supports, some contradicts
        evidence_records = [
            {"source": "SELF_DECLARATION", "supports": True, "notes": "Claims expertise"},
            {"source": "PRACTICAL", "supports": False, "notes": "Observed incorrect procedure"},
            {"source": "SELF_DECLARATION", "supports": True, "notes": "Claims knowledge"},
            {"source": "PRACTICAL", "supports": False, "notes": "Observed another error"},
        ]

        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=competencies,
            evidence_records=evidence_records,
        )

        # With 2 out of 4 evidence contradicting (50%), should trigger conflict review
        assert decision.status == "CONFLICT_REVIEW"
        assert decision.recommended_action == "RESOLVE_EVIDENCE_CONFLICTS"
        assert "HIGH_EVIDENCE_CONFLICT" in decision.reason_codes or "SOME_EVIDENCE_CONFLICT" in decision.reason_codes

    def test_should_abstain_helper(self):
        """Test the simple should_abstain helper function."""
        # Case 1: Should abstain - mandatory NOS with low evidence
        competencies_should_abstain = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 75,
                "evidence_confidence": 0.3,
                "evidence_coverage": 0.2,  # Below 0.4 threshold
            }
        ]

        should_abstain_flag, reasons = should_abstain(
            competencies=competencies_should_abstain,
            threshold_evidence_coverage=0.4,
            threshold_evidence_confidence=0.4,
        )

        assert should_abstain_flag == True
        assert len(reasons) > 0
        assert any("Mandatory NOS" in reason for reason in reasons)

        # Case 2: Should NOT abstain - sufficient evidence
        competencies_should_not_abstain = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 75,
                "evidence_confidence": 0.6,
                "evidence_coverage": 0.7,  # Above threshold
            }
        ]

        should_abstain_flag, reasons = should_abstain(
            competencies=competencies_should_not_abstain,
            threshold_evidence_coverage=0.4,
            threshold_evidence_confidence=0.4,
        )

        assert should_abstain_flag == False
        assert len(reasons) == 0

        # Case 3: High competency but low evidence (should abstain)
        competencies_high_comp_low_ev = [
            {
                "nos_id": "DEMO_NOS_004",
                "mandatory": True,
                "competency_score": 85,  # High
                "evidence_confidence": 0.3,  # Low
                "evidence_coverage": 0.5,  # OK coverage
            }
        ]

        should_abstain_flag, reasons = should_abstain(
            competencies=competencies_high_comp_low_ev,
            threshold_evidence_coverage=0.4,
            threshold_evidence_confidence=0.4,
        )

        assert should_abstain_flag == True
        assert any("high competency" in reason.lower() for reason in reasons)

    def test_abstention_service_integration(self):
        """Test service layer integration."""
        # Test check_evidence_sufficiency service method
        result = AbstentionService.check_evidence_sufficiency(
            worker_id="W001",
            competencies=[
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "competency_score": 70,
                    "evidence_confidence": 0.6,
                    "evidence_coverage": 0.6,
                }
            ],
        )

        assert "status" in result
        assert "confidence" in result
        assert "reason_codes" in result
        assert "reasons" in result
        assert "recommended_action" in result
        assert result["status"] in ["READY_FOR_ASSESSOR", "NEEDS_MORE_EVIDENCE", "ABSTAIN", "CONFLICT_REVIEW"]

        # Test should_abstain service method
        result2 = AbstentionService.should_abstain(
            competencies=[
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "competency_score": 70,
                    "evidence_confidence": 0.3,
                    "evidence_coverage": 0.2,
                }
            ],
        )

        assert "should_abstain" in result2
        assert result2["should_abstain"] == True
        assert isinstance(result2["reason"], str)
        assert isinstance(result2["reasons"], list)

    def test_abstention_edge_cases(self):
        """Test edge cases."""
        # Empty competencies
        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=[],
        )
        assert decision.status == "READY_FOR_ASSESSOR"  # No issues to flag

        # Single competency with all high values
        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=[
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "competency_score": 90,
                    "evidence_confidence": 0.9,
                    "evidence_coverage": 0.95,
                }
            ],
        )
        assert decision.status == "READY_FOR_ASSESSOR"
        assert decision.confidence > 0.7

        # All evidence contradicting
        decision = check_evidence_sufficiency(
            worker_id="W001",
            competencies=[
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "competency_score": 50,
                    "evidence_confidence": 0.5,
                    "evidence_coverage": 0.5,
                }
            ],
            evidence_records=[
                {"source": "PRACTICAL", "supports": False},
                {"source": "PRACTICAL", "supports": False},
                {"source": "PRACTICAL", "supports": False},
            ]
        )
        # Should be conflict review or abstain depending on other factors
        assert decision.status in ["CONFLICT_REVIEW", "ABSTAIN", "NEEDS_MORE_EVIDENCE"]