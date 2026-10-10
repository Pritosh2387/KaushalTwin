"""
KaushalTwin ML Service — Service: Assessor Calibration + Consistency (Module 8)
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from ml.algorithms.calibration import calculate_assessor_calibration, AssessorProfile, CalibrationResult


class CalibrationService:
    """Service for assessor calibration and consistency analysis."""

    @staticmethod
    def calculate_assessor_calibration(
        assessor_scores: List[Dict[str, Any]],
        competency_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate assessor calibration and consistency metrics.

        Args:
            assessor_scores: List of assessment records from multiple assessors
            competency_areas: Specific competency areas to analyze (optional)

        Returns:
            Dictionary with calibration results
        """
        result = calculate_assessor_calibration(
            assessor_scores=assessor_scores,
            competency_areas=competency_areas,
        )
        # Convert dataclasses to dicts for JSON serialization
        return {
            "assessor_profiles": [
                {
                    "assessor_id": profile.assessor_id,
                    "mean_score": profile.mean_score,
                    "group_mean": profile.group_mean,
                    "severity_delta": profile.severity_delta,
                    "interpretation": profile.interpretation,
                    "score_variance": profile.score_variance,
                    "total_assessments": profile.total_assessments,
                }
                for profile in result.assessor_profiles
            ],
            "agreement_metrics": result.agreement_metrics,
            "disagreement_areas": result.disagreement_areas,
            "overall_consistency": result.overall_consistency,
            "recommended_actions": result.recommended_actions,
        }

    @staticmethod
    def get_assessor_profile(
        assessor_scores: List[Dict[str, Any]],
        assessor_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get profile for a specific assessor.

        Args:
            assessor_scores: List of assessment records
            assessor_id: ID of assessor to profile

        Returns:
            Assessor profile dictionary or None if not found
        """
        result = CalibrationService.calculate_assessor_calibration(assessor_scores)
        for profile in result["assessor_profiles"]:
            if profile["assessor_id"] == assessor_id:
                return profile
        return None

    @staticmethod
    def calculate_agreement_between_assessors(
        assessor_a_scores: List[Dict[str, Any]],
        assessor_b_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate agreement between two specific assessors.

        Args:
            assessor_a_scores: Scores from first assessor
            assessor_b_scores: Scores from second assessor

        Returns:
            Agreement metrics between the two assessors
        """
        combined_scores = assessor_a_scores + assessor_b_scores
        result = CalibrationService.calculate_assessor_calibration(combined_scores)

        # Extract just the two assessors we care about
        assessor_profiles = [
            p for p in result["assessor_profiles"]
            if p["assessor_id"] in [assessor_a_scores[0].get("assessor_id") if assessor_a_scores else "unknown",
                                  assessor_b_scores[0].get("assessor_id") if assessor_b_scores else "unknown"]
        ]

        return {
            "assessor_profiles": assessor_profiles,
            "agreement_metrics": result["agreement_metrics"],
            "overall_consistency": result["overall_consistency"],
        }