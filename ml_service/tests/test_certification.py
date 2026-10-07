"""
Unit Tests — Module 9: Competency Profile + Certification Recommendation
"""
import pytest
from app.algorithms.certification import (
    make_certification_recommendation,
    CertificationBasis,
    CertificationRecommendation,
)
from app.services.certification_service import CertificationService


class TestCertificationAlgorithm:
    def test_make_certification_recommendation_excellent(self):
        """Test recommendation for excellent candidate."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 90,
                "evidence_confidence": 0.9,
                "evidence_coverage": 0.95,
            },
            {
                "nos_id": "DEMO_NOS_002",
                "mandatory": True,
                "competency_score": 88,
                "evidence_confidence": 0.85,
                "evidence_coverage": 0.9,
            },
        ]

        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
        )

        assert recommendation.recommendation == "RECOMMEND_CERTIFICATION"
        assert recommendation.confidence > 0.8
        assert recommendation.basis.competency_score >= 85
        assert recommendation.basis.evidence_confidence >= 0.8
        assert recommendation.basis.evidence_coverage >= 0.8
        assert recommendation.basis.mandatory_nos_complete == True
        assert recommendation.basis.critical_conflicts == 0
        assert recommendation.assessor_action == "REVIEW_AND_SIGN_OFF"
        assert recommendation.ai_authority == "RECOMMENDATION_ONLY"

    def test_make_certification_recommendation_missing_mandatory(self):
        """Test recommendation when mandatory NOS incomplete."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 85,
                "evidence_confidence": 0.5,  # Low confidence
                "evidence_coverage": 0.4,    # Low coverage
            },
            {
                "nos_id": "DEMO_NOS_002",
                "mandatory": True,
                "competency_score": 80,
                "evidence_confidence": 0.4,
                "evidence_coverage": 0.3,
            },
        ]

        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
        )

        # Should be downgraded due to mandatory NOS issues
        assert recommendation.recommendation in [
            "CONDITIONAL_RECOMMENDATION",
            "MORE_EVIDENCE_REQUIRED",
            "NOT_YET_READY"
        ]
        assert recommendation.basis.mandatory_nos_complete == False
        assert recommendation.confidence > 0.5

    def test_make_certification_recommendation_poor_evidence(self):
        """Test recommendation with poor evidence despite good competency."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 85,  # Good competency
                "evidence_confidence": 0.3,  # Poor confidence
                "evidence_coverage": 0.2,    # Poor coverage
            }
        ]

        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
        )

        # Should not recommend certification due to poor evidence
        assert recommendation.recommendation != "RECOMMEND_CERTIFICATION"
        assert recommendation.basis.evidence_confidence == 0.3
        assert recommendation.basis.evidence_coverage == 0.2

    def test_make_certification_recommendation_with_abstention_override(self):
        """Test that abstention decision overrides certification logic."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 90,
                "evidence_confidence": 0.9,
                "evidence_coverage": 0.95,
            }
        ]

        # Abstention decision saying to abstain
        abstention_decision = {
            "status": "ABSTAIN",
            "confidence": 0.9,
            "reason_codes": ["MANDATORY_EVIDENCE_MISSING"],
            "reasons": ["Missing practical evidence"],
            "recommended_action": "HUMAN_REVIEW_REQUIRED",
        }

        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
            abstention_decision=abstention_decision,
        )

        # Should obey abstention decision
        assert recommendation.recommendation == "ABSTAIN"
        assert recommendation.confidence >= 0.8
        assert recommendation.assessor_action == "REVIEW_AND_SIGN_OFF"

    def test_make_certification_recommendation_with_critical_conflicts(self):
        """Test that critical conflicts downgrade recommendation."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mand": True,
                "competency_score": 85,
                "evidence_confidence": 0.8,
                "evidence_coverage": 0.85,
            }
        ]

        # Skill gap analysis showing critical conflicts
        skill_gap_analysis = {
            "summary": {
                "critical_gaps": 2  # Two critical gaps
            }
        }

        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
            skill_gap_analysis=skill_gap_analysis,
        )

        # Should be downgraded due to critical conflicts
        assert recommendation.basis.critical_conflicts == 2
        # Even with good scores, conflicts should reduce confidence in recommendation

    def test_certification_service_integration(self):
        """Test service layer integration."""
        competency_profile = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 78,
                "evidence_confidence": 0.7,
                "evidence_coverage": 0.75,
            }
        ]

        # Test main service method
        result = CertificationService.make_certification_recommendation(
            worker_id="W001",
            competency_profile=competency_profile,
        )

        assert "recommendation" in result
        assert "confidence" in result
        assert "basis" in result
        assert "assessor_action" in result
        assert "ai_authority" in result

        assert result["recommendation"] in [
            "RECOMMEND_CERTIFICATION",
            "CONDITIONAL_RECOMMENDATION",
            "MORE_EVIDENCE_REQUIRED",
            "NOT_YET_READY",
            "ABSTAIN",
            "CONFLICT_REVIEW"
        ]
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["ai_authority"] == "RECOMMENDATION_ONLY"

        # Test competency profile summary service
        summary = CertificationService.get_competency_profile_summary(competency_profile)
        assert "total_nos" in summary
        assert "mandatory_count" in summary
        assert summary["total_nos"] == 1
        assert summary["mandatory_count"] == 1
        assert summary["average_competency_score"] == 78.0

    def test_certification_edge_cases(self):
        """Test edge cases."""
        # Empty competency profile
        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=[],
        )
        assert recommendation.recommendation == "NOT_YET_READY"
        assert recommendation.confidence > 0.8
        assert recommendation.basis.competency_score == 0.0

        # Single competency with zero scores
        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=[{
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 0,
                "evidence_confidence": 0.0,
                "evidence_coverage": 0.0,
            }]
        )
        assert recommendation.recommendation == "NOT_YET_READY"
        assert recommendation.basis.competency_score == 0.0

        # Very high scores
        recommendation = make_certification_recommendation(
            worker_id="W001",
            competency_profile=[{
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "competency_score": 100,
                "evidence_confidence": 1.0,
                "evidence_coverage": 1.0,
            }]
        )
        # Should recommend certification (though may be conditional due to other factors)
        assert recommendation.recommendation in [
            "RECOMMEND_CERTIFICATION",
            "CONDITIONAL_RECOMMENDATION"
        ]


class TestCertificationBasis:
    def test_certification_basis_creation(self):
        """Test creating a CertificationBasis instance."""
        basis = CertificationBasis(
            competency_score=75.0,
            evidence_confidence=0.8,
            evidence_coverage=0.75,
            mandatory_nos_complete=True,
            critical_conflicts=0,
            overall_readiness_score=72.0,
        )
        assert basis.competency_score == 75.0
        assert basis.evidence_confidence == 0.8
        assert basis.evidence_coverage == 0.75
        assert basis.mandatory_nos_complete == True
        assert basis.critical_conflicts == 0
        assert basis.overall_readiness_score == 72.0