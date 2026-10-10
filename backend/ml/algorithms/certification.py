"""
KaushalTwin ML Service — Algorithm: Competency Profile + Certification Recommendation (Module 9)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CertificationBasis:
    """Basis for certification recommendation."""
    competency_score: float  # 0-100
    evidence_confidence: float  # 0.0-1.0
    evidence_coverage: float  # 0.0-1.0
    mandatory_nos_complete: bool  # Whether all mandatory NOS are adequately covered
    critical_conflicts: int  # Number of critical evidence conflicts
    overall_readiness_score: float  # Composite score for readiness


@dataclass
class CertificationRecommendation:
    """Certification recommendation result."""
    recommendation: str  # See possible values below
    confidence: float  # 0.0-1.0 confidence in recommendation
    basis: CertificationBasis
    assessor_action: str  # Suggested action for assessor
    ai_authority: str  # Clarifies AI's role (always recommendation only)


def make_certification_recommendation(
    worker_id: str,
    competency_profile: List[Dict[str, Any]],
    skill_gap_analysis: Optional[Dict[str, Any]] = None,
    abstention_decision: Optional[Dict[str, Any]] = None,
    calibration_info: Optional[Dict[str, Any]] = None,
) -> CertificationRecommendation:
    """
    Make a certification recommendation based on all available information.

    Implements Module 9: Competency Profile + Certification Recommendation.
    Generates CERTIFICATION RECOMMENDATION (not actual certification).

    Args:
        worker_id: Worker identifier
        competency_profile: List of competency dictionaries from competency twin
        skill_gap_analysis: Results from skill gap analysis (optional)
        abstention_decision: Results from abstention/evidence sufficiency check (optional)
        calibration_info: Results from assessor calibration (optional)

    Returns:
        CertificationRecommendation with recommendation, confidence, basis, etc.
    """
    if skill_gap_analysis is None:
        skill_gap_analysis = {}
    if abstention_decision is None:
        abstention_decision = {}
    if calibration_info is None:
        calibration_info = {}

    # Extract key metrics from competency profile
    if not competency_profile:
        # No competency data - cannot make recommendation
        return CertificationRecommendation(
            recommendation="NOT_YET_READY",
            confidence=0.9,  # High confidence in this assessment
            basis=CertificationBasis(
                competency_score=0.0,
                evidence_confidence=0.0,
                evidence_coverage=0.0,
                mandatory_nos_complete=False,
                critical_conflicts=0,
                overall_readiness_score=0.0,
            ),
            assessor_action="COLLECT_MORE_EVIDENCE",
            ai_authority="RECOMMENDATION_ONLY",
        )

    # Calculate average competency score
    competency_scores = [c.get("competency_score", 0) for c in competency_profile if c.get("competency_score") is not None]
    avg_competency_score = sum(competency_scores) / len(competency_scores) if competency_scores else 0.0

    # Calculate average evidence confidence and coverage
    evidence_confidences = [c.get("evidence_confidence", 0.0) or 0.0 for c in competency_profile]
    evidence_coverages = [c.get("evidence_coverage", 0.0) for c in competency_profile]

    avg_evidence_confidence = sum(evidence_confidences) / len(evidence_confidences) if evidence_confidences else 0.0
    avg_evidence_coverage = sum(evidence_coverages) / len(evidence_coverages) if evidence_coverages else 0.0

    # Check mandatory NOS completeness
    mandatory_nos = [c for c in competency_profile if c.get("mandatory", False)]
    mandatory_nos_complete = True
    if mandatory_nos:
        # Consider mandatory NOS complete if average coverage >= 0.7 and confidence >= 0.6
        mandatory_coverages = [c.get("evidence_coverage", 0.0) for c in mandatory_nos]
        mandatory_confidences = [(c.get("evidence_confidence", 0.0) or 0.0) for c in mandatory_nos]

        if mandatory_coverages and mandatory_confidences:
            avg_mandatory_coverage = sum(mandatory_coverages) / len(mandatory_coverages)
            avg_mandatory_confidence = sum(mandatory_confidences) / len(mandatory_confidences)
            mandatory_nos_complete = (avg_mandatory_coverage >= 0.7) and (avg_mandatory_confidence >= 0.6)
        else:
            mandatory_nos_complete = False

    # Count critical conflicts from skill gap analysis
    critical_conflicts = skill_gap_analysis.get("summary", {}).get("critical_gaps", 0)

    # Calculate overall readiness score (weighted composite)
    # Weights: competency (40%), evidence confidence (30%), evidence coverage (30%)
    readiness_score = (
        (avg_competency_score / 100.0) * 0.4 +
        avg_evidence_confidence * 0.3 +
        avg_evidence_coverage * 0.3
    ) * 100  # Convert back to 0-100 scale

    # Adjust readiness based on mandatory NOS and conflicts
    if not mandatory_nos_complete:
        readiness_score *= 0.7  # Penalty for incomplete mandatory NOS
    if critical_conflicts > 0:
        readiness_score *= (0.8 ** critical_conflicts)  # Exponential penalty for conflicts

    # Ensure readiness score is in valid range
    readiness_score = max(0.0, min(100.0, readiness_score))

    # Determine recommendation based on readiness score and other factors
    recommendation, confidence, assessor_action = _determine_recommendation(
        readiness_score=readiness_score,
        avg_competency_score=avg_competency_score,
        avg_evidence_confidence=avg_evidence_confidence,
        avg_evidence_coverage=avg_evidence_coverage,
        mandatory_nos_complete=mandatory_nos_complete,
        critical_conflicts=critical_conflicts,
        abstention_decision=abstention_decision,
    )

    basis = CertificationBasis(
        competency_score=avg_competency_score,
        evidence_confidence=avg_evidence_confidence,
        evidence_coverage=avg_evidence_coverage,
        mandatory_nos_complete=mandatory_nos_complete,
        critical_conflicts=critical_conflicts,
        overall_readiness_score=readiness_score,
    )

    return CertificationRecommendation(
        recommendation=recommendation,
        confidence=confidence,
        basis=basis,
        assessor_action=assessor_action,
        ai_authority="RECOMMENDATION_ONLY",
    )


def _determine_recommendation(
    readiness_score: float,
    avg_competency_score: float,
    avg_evidence_confidence: float,
    avg_evidence_coverage: float,
    mandatory_nos_complete: bool,
    critical_conflicts: int,
    abstention_decision: Dict[str, Any],
) -> Tuple[str, float, str]:
    """
    Determine the certification recommendation based on readiness and constraints.
    """
    # Check abstention decision first - overrides other considerations
    abstention_status = abstention_decision.get("status", "READY_FOR_ASSESSOR")
    if abstention_status == "ABSTAIN":
        return (
            "ABSTAIN",
            0.9,  # High confidence in abstention decision
            "REVIEW_AND_SIGN_OFF"  # Assessor should review why AI abstained
        )
    elif abstention_status == "CONFLICT_REVIEW":
        return (
            "CONFLICT_REVIEW",
            0.85,
            "RESOLVE_EVIDENCE_CONFLICTS_FIRST"
        )
    elif abstention_status == "NEEDS_MORE_EVIDENCE":
        # Not an immediate override, but will affect recommendation below
        pass

    # Define recommendation thresholds
    # These are prototype thresholds - would need calibration with real data
    EXCELLENT_THRESHOLD = 85
    GOOD_THRESHOLD = 70
    FAIR_THRESHOLD = 55
    POOR_THRESHOLD = 40

    # Determine base recommendation from readiness score
    if readiness_score >= EXCELLENT_THRESHOLD:
        base_recommendation = "RECOMMEND_CERTIFICATION"
        base_confidence = 0.9
        base_action = "REVIEW_AND_SIGN_OFF"
    elif readiness_score >= GOOD_THRESHOLD:
        base_recommendation = "CONDITIONAL_RECOMMENDATION"
        base_confidence = 0.8
        base_action = "REVIEW_WITH_CONDITIONS"
    elif readiness_score >= FAIR_THRESHOLD:
        base_recommendation = "MORE_EVIDENCE_REQUIRED"
        base_confidence = 0.75
        base_action = "RUN_TARGETED_ASSESSMENT"
    elif readiness_score >= POOR_THRESHOLD:
        base_recommendation = "NOT_YET_READY"
        base_confidence = 0.7
        base_action = "DEVELOP_SKILLS_FURTHER"
    else:
        base_recommendation = "NOT_YET_READY"
        base_confidence = 0.8
        base_action = "SIGNIFICANT_SKILL_DEVELOPMENT_NEEDED"

    # Apply adjustments based on specific factors
    final_confidence = base_confidence
    final_recommendation = base_recommendation
    final_action = base_action

    # If mandatory NOS incomplete, downgrade recommendation
    if not mandatory_nos_complete:
        if final_recommendation == "RECOMMEND_CERTIFICATION":
            final_recommendation = "CONDITIONAL_RECOMMENDATION"
            final_confidence *= 0.9
            final_action = "ADDRESS_MANDATORY_GAPS_THEN_REVIEW"
        elif final_recommendation == "CONDITIONAL_RECOMMENDATION":
            final_recommendation = "MORE_EVIDENCE_REQUIRED"
            final_confidence *= 0.85
            final_action = "COMPLETE_MANDATORY_REQUIREMENTS"

    # If we have critical conflicts, be more cautious
    if critical_conflicts > 0:
        if final_recommendation in ["RECOMMEND_CERTIFICATION", "CONDITIONAL_RECOMMENDATION"]:
            # Downgrade by one level
            if final_recommendation == "RECOMMEND_CERTIFICATION":
                final_recommendation = "CONDITIONAL_RECOMMENDATION"
            elif final_recommendation == "CONDITIONAL_RECOMMENDATION":
                final_recommendation = "MORE_EVIDENCE_REQUIRED"
            final_confidence *= 0.9
            final_action = "RESOLVE_CONFLICTS_THEN_RECONSIDER"

    # If abstention suggested needing more evidence, align with that
    if abstention_status == "NEEDS_MORE_EVIDENCE" and final_recommendation in [
        "RECOMMEND_CERTIFICATION",
        "CONDITIONAL_RECOMMENDATION"
    ]:
        final_recommendation = "MORE_EVIDENCE_REQUIRED"
        final_action = "RUN_TARGETED_ASSESSMENT"
        final_confidence = min(final_confidence, 0.8)  # Cap confidence

    # Ensure we don't recommend certification without sufficient evidence
    if (final_recommendation == "RECOMMEND_CERTIFICATION" and
        (avg_evidence_coverage < 0.5 or avg_evidence_confidence < 0.5)):
        final_recommendation = "MORE_EVIDENCE_REQUIRED"
        final_action = "GATHER_MORE_EVIDENCE_BEFORE_RECOMMENDING"
        final_confidence = 0.75

    # Map confidence to appropriate range (0.5-0.95 for most cases)
    final_confidence = max(0.5, min(0.95, final_confidence))

    return final_recommendation, final_confidence, final_action