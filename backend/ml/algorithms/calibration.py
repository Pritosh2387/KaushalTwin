"""
KaushalTwin ML Service — Algorithm: Assessor Calibration + Consistency (Module 8)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
import math
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class AssessorProfile:
    """Profile of an assessor's scoring tendencies."""
    assessor_id: str
    mean_score: float
    group_mean: float
    severity_delta: float  # positive = lenient, negative = strict
    interpretation: str  # e.g., "RELATIVELY STRICT", "RELATIVELY LENIENT"
    score_variance: float
    total_assessments: int


@dataclass
class CalibrationResult:
    """Result of assessor calibration analysis."""
    assessor_profiles: List[AssessorProfile]
    agreement_metrics: Dict[str, Any]
    disagreement_areas: List[str]
    overall_consistency: str
    recommended_actions: List[str]


def calculate_assessor_calibration(
    assessor_scores: List[Dict[str, Any]],
    competency_areas: Optional[List[str]] = None,
) -> CalibrationResult:
    """
    Analyze assessor calibration and consistency.

    Implements Module 8: Assessor Calibration + Consistency.
    Helps assessors score candidates consistently by identifying scoring differences.

    Args:
        assessor_scores: List of assessment records, each containing:
            - assessor_id: str
            - worker_id: str
            - competency_area: str (e.g., "safety", "installation")
            - score: float or int (the assessor's score)
        competency_areas: List of competency areas to analyze (if None, use all)

    Returns:
        CalibrationResult with assessor profiles, agreement metrics, etc.
    """
    if not assessor_scores:
        return CalibrationResult(
            assessor_profiles=[],
            agreement_metrics={},
            disagreement_areas=[],
            overall_consistency="NO_DATA",
            recommended_actions=["Collect assessment data for calibration analysis"]
        )

    # Group scores by assessor and competency area
    assessor_data = defaultdict(lambda: defaultdict(list))
    all_competency_areas = set()

    for record in assessor_scores:
        assessor_id = record.get("assessor_id")
        worker_id = record.get("worker_id")
        competency_area = record.get("competency_area", "general")
        score = record.get("score")

        if assessor_id is None or worker_id is None or score is None:
            continue

        try:
            score_val = float(score)
            assessor_data[assessor_id][competency_area].append(score_val)
            all_competency_areas.add(competency_area)
        except (ValueError, TypeError):
            continue

    if competency_areas is not None:
        all_competency_areas = set(competency_areas) & all_competency_areas
        if not all_competency_areas:
            all_competency_areas = {"general"}

    # Calculate assessor profiles
    assessor_profiles = []
    all_scores = []  # For calculating group means

    for assessor_id, competency_dict in assessor_data.items():
        # Flatten all scores for this assessor across competencies
        assessor_all_scores = []
        for scores in competency_dict.values():
            assessor_all_scores.extend(scores)

        if not assessor_all_scores:
            continue

        assessor_mean = sum(assessor_all_scores) / len(assessor_all_scores)
        all_scores.extend(assessor_all_scores)

        # Calculate variance
        variance = sum((x - assessor_mean) ** 2 for x in assessor_all_scores) / len(assessor_all_scores)

        assessor_profiles.append(
            AssessorProfile(
                assessor_id=assessor_id,
                mean_score=assessor_mean,
                group_mean=0.0,  # Will calculate after loop
                severity_delta=0.0,  # Will calculate after loop
                interpretation="CALCULATING",
                score_variance=variance,
                total_assessments=len(assessor_all_scores),
            )
        )

    # Calculate group mean and adjust profiles
    if all_scores:
        group_mean = sum(all_scores) / len(all_scores)

        for profile in assessor_profiles:
            profile.group_mean = group_mean
            profile.severity_delta = profile.mean_score - group_mean

            # Interpret severity delta
            if abs(profile.severity_delta) < 0.5:
                profile.interpretation = "CONSISTENT_WITH_GROUP"
            elif profile.severity_delta > 0.5:
                profile.interpretation = "RELATIVELY_LENIENT"
            else:  # severity_delta < -0.5
                profile.interpretation = "RELATIVELY_STRICT"

    # Calculate agreement metrics
    agreement_metrics = _calculate_agreement_metrics(assessor_data, all_competency_areas)

    # Identify disagreement areas
    disagreement_areas = _identify_disagreement_areas(assessor_data, all_competency_areas)

    # Overall consistency assessment
    overall_consistency = _assess_overall_consistency(agreement_metrics, assessor_profiles)

    # Generate recommended actions
    recommended_actions = _generate_calibration_recommendations(
        assessor_profiles, agreement_metrics, disagreement_areas
    )

    return CalibrationResult(
        assessor_profiles=assessor_profiles,
        agreement_metrics=agreement_metrics,
        disagreement_areas=disagreement_areas,
        overall_consistency=overall_consistency,
        recommended_actions=recommended_actions,
    )


def _calculate_agreement_metrics(
    assessor_data: Dict[str, Dict[str, List[float]]],
    competency_areas: set,
) -> Dict[str, Any]:
    """Calculate inter-assessor agreement metrics."""
    metrics = {
        "competency_areas": list(competency_areas),
        "area_metrics": {},
    }

    # For each competency area, calculate agreement statistics
    for area in competency_areas:
        # Collect scores for this area by assessor
        assessor_scores_for_area = []
        assessor_ids_with_data = []

        for assessor_id, competency_dict in assessor_data.items():
            if area in competency_dict and competency_dict[area]:
                assessor_scores_for_area.append(competency_dict[area])
                assessor_ids_with_data.append(assessor_id)

        if len(assessor_ids_with_data) < 2:
            # Need at least 2 assessors with data for agreement metrics
            metrics["area_metrics"][area] = {
                "assessors_with_data": len(assessor_ids_with_data),
                "percentage_agreement": None,
                "mean_absolute_difference": None,
                "note": "Insufficient data for agreement calculation (need ≥2 assessors)",
            }
            continue

        # Calculate percentage agreement (exact score matches)
        # For simplicity, we'll consider scores within 0.5 points as "in agreement"
        all_scores_for_area = [score for scores in assessor_scores_for_area for score in scores]
        if not all_scores_for_area:
            continue

        # Mean score for the area
        mean_score = sum(all_scores_for_area) / len(all_scores_for_area)

        # Mean absolute difference from mean (simpler than pairwise for now)
        mad = sum(abs(score - mean_score) for score in all_scores_for_area) / len(all_scores_for_area)

        # Rough percentage agreement: percentage of scores within 1 point of mean
        scores_within_range = [s for s in all_scores_for_area if abs(s - mean_score) <= 1.0]
        percentage_agreement = (len(scores_within_range) / len(all_scores_for_area)) * 100 if all_scores_for_area else 0

        metrics["area_metrics"][area] = {
            "assessors_with_data": len(assessor_ids_with_data),
            "mean_score": mean_score,
            "mean_absolute_difference": mad,
            "percentage_agreement": percentage_agreement,
            "total_observations": len(all_scores_for_area),
        }

    # Overall metrics
    if metrics["area_metrics"]:
        valid_areas = [area for area, data in metrics["area_metrics"].items()
                      if data["percentage_agreement"] is not None]
        if valid_areas:
            avg_percentage_agreement = sum(
                metrics["area_metrics"][area]["percentage_agreement"]
                for area in valid_areas
            ) / len(valid_areas)
            metrics["overall_percentage_agreement"] = avg_percentage_agreement
        else:
            metrics["overall_percentage_agreement"] = None
    else:
        metrics["overall_percentage_agreement"] = None

    return metrics


def _identify_disagreement_areas(
    assessor_data: Dict[str, Dict[str, List[float]]],
    competency_areas: set,
) -> List[str]:
    """Identify competency areas with high assessor disagreement."""
    disagreement_areas = []

    for area in competency_areas:
        # Get mean score for each assessor in this area
        assessor_means = []
        for assessor_id, competency_dict in assessor_data.items():
            if area in competency_dict and competency_dict[area]:
                scores = competency_dict[area]
                if scores:
                    assessor_mean = sum(scores) / len(scores)
                    assessor_means.append(assessor_mean)

        # If we have at least 2 assessors with data, check for disagreement
        if len(assessor_means) >= 2:
            mean_of_means = sum(assessor_means) / len(assessor_means)
            # Standard deviation of assessor means
            if len(assessor_means) > 1:
                variance_of_means = sum((x - mean_of_means) ** 2 for x in assessor_means) / (len(assessor_means) - 1)
                std_of_means = math.sqrt(variance_of_means) if variance_of_means >= 0 else 0.0
                # If standard deviation is more than 15% of the mean range, flag as disagreement area
                if mean_of_means != 0 and std_of_means / abs(mean_of_means) > 0.15:
                    disagreement_areas.append(area)

    return disagreement_areas


def _assess_overall_consistency(
    agreement_metrics: Dict[str, Any],
    assessor_profiles: List[AssessorProfile],
) -> str:
    """Assess overall consistency level."""
    if not assessor_profiles:
        return "NO_ASSESSORS"

    overall_agreement = agreement_metrics.get("overall_percentage_agreement")
    if overall_agreement is None:
        return "INSUFFICIENT_DATA"

    if overall_agreement >= 80:
        return "HIGH_CONSISTENCY"
    elif overall_agreement >= 60:
        return "MODERATE_CONSISTENCY"
    elif overall_agreement >= 40:
        return "LOW_CONSISTENCY"
    else:
        return "VERY_LOW_CONSISTENCY"


def _generate_calibration_recommendations(
    assessor_profiles: List[AssessorProfile],
    agreement_metrics: Dict[str, Any],
    disagreement_areas: List[str],
) -> List[str]:
    """Generate recommended actions based on calibration analysis."""
    recommendations = []

    if not assessor_profiles:
        recommendations.append("Collect assessment data from assessors to enable calibration analysis")
        return recommendations

    # Check for assessors with extreme severity
    extreme_assessors = [
        p for p in assessor_profiles
        if abs(p.severity_delta) > 2.0  # More than 2 points from group mean
    ]
    if extreme_assessors:
        assessor_names = [p.assessor_id for p in extreme_assessors]
        recommendations.append(
            f"Assessors {', '.join(assessor_names)} show extreme scoring tendencies "
            f"consider retraining or recalibration"
        )

    # Check for high variance assessors
    high_variance_assessors = [
        p for p in assessor_profiles
        if p.score_variance > 4.0  # Variance > 4 (std dev > 2)
    ]
    if high_variance_assessors:
        assessor_names = [p.assessor_id for p in high_variance_assessors]
        recommendations.append(
            f"Assessors {', '.join(assessor_names)} show high score variability "
            f"consider using scoring rubrics or anchor examples"
        )

    # Check disagreement areas
    if disagreement_areas:
        recommendations.append(
            f"High disagreement detected in areas: {', '.join(disagreement_areas)}. "
            f"Consider creating detailed scoring guidelines for these competencies."
        )

    # Overall consistency recommendation
    overall_consistency = _assess_overall_consistency(agreement_metrics, assessor_profiles)
    if overall_consistency in ["LOW_CONSISTENCY", "VERY_LOW_CONSISTENCY"]:
        recommendations.append(
            "Overall assessor consistency is low. Consider implementing regular calibration sessions "
            "and using standardized scoring rubrics."
        )
    elif overall_consistency == "MODERATE_CONSISTENCY":
        recommendations.append(
            "Assessor consistency is moderate. Periodic calibration checks recommended."
        )

    if not recommendations:
        recommendations.append(
            "Assessor calibration shows good consistency. Continue current practices."
        )

    return recommendations