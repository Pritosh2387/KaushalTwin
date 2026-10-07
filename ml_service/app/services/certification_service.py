"""
KaushalTwin ML Service — Service: Competency Profile + Certification Recommendation (Module 9)
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from app.algorithms.certification import make_certification_recommendation, CertificationRecommendation


class CertificationService:
    """Service for certification recommendation and competency profiling."""

    @staticmethod
    def make_certification_recommendation(
        worker_id: str,
        competency_profile: List[Dict[str, Any]],
        skill_gap_analysis: Optional[Dict[str, Any]] = None,
        abstention_decision: Optional[Dict[str, Any]] = None,
        calibration_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a certification recommendation based on all available information.

        Args:
            worker_id: Worker identifier
            competency_profile: List of competency dictionaries from competency twin
            skill_gap_analysis: Results from skill gap analysis (optional)
            abstention_decision: Results from abstention/evidence sufficiency check (optional)
            calibration_info: Results from assessor calibration (optional)

        Returns:
            Dictionary with certification recommendation
        """
        recommendation = make_certification_recommendation(
            worker_id=worker_id,
            competency_profile=competency_profile,
            skill_gap_analysis=skill_gap_analysis,
            abstention_decision=abstention_decision,
            calibration_info=calibration_info,
        )
        # Convert dataclass to dict for JSON serialization
        return {
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "basis": {
                "competency_score": recommendation.basis.competency_score,
                "evidence_confidence": recommendation.basis.evidence_confidence,
                "evidence_coverage": recommendation.basis.evidence_coverage,
                "mandatory_nos_complete": recommendation.basis.mandatory_nos_complete,
                "critical_conflicts": recommendation.basis.critical_conflicts,
                "overall_readiness_score": recommendation.basis.overall_readiness_score,
            },
            "assessor_action": recommendation.assessor_action,
            "ai_authority": recommendation.ai_authority,
        }

    @staticmethod
    def get_competency_profile_summary(
        competency_profile: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get a summary of the competency profile.

        Args:
            competency_profile: List of competency dictionaries

        Returns:
            Summary dictionary
        """
        if not competency_profile:
            return {
                "total Sánchez": 0,
                "mandatory_count": 0,
                "average_competency_score": 0.0,
                "average_evidence_confidence": 0.0,
                "average_evidence_coverage": 0.0,
            }

        mandatory_count = len([c for c in competency_profile if c.get("mandatory", False)])
        competency_scores = [c.get("competency_score", 0) for c in competency_profile if c.get("competency_score") is not None]
        evidence_confidences = [c.get("evidence_confidence", 0.0) or 0.0 for c in competency_profile]
        evidence_coverages = [c.get("evidence_coverage", 0.0) for c in competency_profile]

        return {
            "total_nos": len(competency_profile),
            "mandatory_count": mandatory_count,
            "average_competency_score": sum(competency_scores) / len(competency_scores) if competency_scores else 0.0,
            "average_evidence_confidence": sum(evidence_confidences) / len(evidence_confidences) if evidence_confidences else 0.0,
            "average_evidence_coverage": sum(evidence_coverages) / len(evidence_coverages) if evidence_coverages else 0.0,
            "competency_distribution": {
                "excellent": len([s for s in competency_scores if s >= 85]),
                "good": len([s for s in competency_scores if 70 <= s < 85]),
                "fair": len([s for s in competency_scores if 55 <= s < 70]),
                "poor": len([s for s in competency_scores if s < 55]),
            }
        }