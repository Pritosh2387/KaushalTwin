"""
KaushalTwin ML Service — Algorithm: Abstention / Evidence Sufficiency Engine (Module 7)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AbstentionDecision:
    """Result of abstention/evidence sufficiency check."""
    status: str  # "READY_FOR_ASSESSOR", "NEEDS_MORE_EVIDENCE", "ABSTAIN", "CONFLICT_REVIEW"
    confidence: float  # 0.0-1.0 confidence in the decision
    reason_codes: List[str]  # Standardized reason codes
    reasons: List[str]  # Human-readable explanations
    recommended_action: str  # Suggested next step
    next_task_id: Optional[str] = None  # ID of recommended task if applicable
    metadata: Dict[str, Any] = None  # Additional context


def check_evidence_sufficiency(
    worker_id: str,
    competencies: List[Dict[str, Any]],
    evidence_records: Optional[List[Dict[str, Any]]] = None,
    assessment_task_results: Optional[List[Dict[str, Any]]] = None,
    assessor_observations: Optional[List[Dict[str, Any]]] = None,
) -> AbstentionDecision:
    """
    Determine if there is sufficient evidence to proceed with assessment recommendation.

    Implements Module 7: Abstention / Evidence Sufficiency Engine.

    Args:
        worker_id: Worker identifier
        competencies: List of competency dictionaries from competency twin
        evidence_records: List of evidence records
        assessment_task_results: Results from completed assessment tasks
        assessor_observations: Direct observations by assessors

    Returns:
        AbstentionDecision with status, confidence, reasons, and recommended action
    """
    if evidence_records is None:
        evidence_records = []
    if assessment_task_results is None:
        assessment_task_results = []
    if assessor_observations is None:
        assessor_observations = []

    # Initialize decision components
    reason_codes = []
    reasons = []
    risk_factors = []
    strength_factors = []
    next_task_id = None  # Initialize early to avoid UnboundLocalError

    # Analyze each competency/NOS
    mandatory_nos = [c for c in competencies if c.get("mandatory", False)]
    optional_nos = [c for c in competencies if not c.get("mandatory", False)]

    # Check 1: Mandatory NOS with insufficient evidence
    mandatory_evidence_issues = []
    for nos in mandatory_nos:
        nos_id = nos.get("nos_id", "unknown")
        evidence_confidence = nos.get("evidence_confidence", 0.0) or 0.0
        evidence_coverage = nos.get("evidence_coverage", 0.0)
        competency_score = nos.get("competency_score", 0)

        # Mandatory NOS requires sufficient evidence coverage and confidence
        # Using thresholds from should_abstain helper for consistency
        if evidence_coverage < 0.4:
            mandatory_evidence_issues.append(
                f"Mandatory NOS {nos_id} has insufficient evidence coverage ({evidence_coverage:.0%})"
            )
            reason_codes.append("MANDATORY_EVIDENCE_MISSING")
            risk_factors.append(f"low_coverage_{nos_id}")

        if evidence_confidence < 0.4:
            mandatory_evidence_issues.append(
                f"Mandatory NOS {nos_id} has low evidence confidence ({evidence_confidence:.0%})"
            )
            reason_codes.append("LOW_EVIDENCE_CONFIDENCE")
            risk_factors.append(f"low_confidence_{nos_id}")

        # High competency but low evidence is especially problematic
        if competency_score >= 70 and evidence_confidence < 0.4:
            mandatory_evidence_issues.append(
                f"Mandatory NOS {nos_id} shows high competency ({competency_score}) but low evidence confidence"
            )
            reason_codes.append("HIGH_COMPETENCY_LOW_EVIDENCE")
            risk_factors.append(f"competency_evidence_mismatch_{nos_id}")

    # Add mandatory NOS specific issues to main reasons list
    reasons.extend(mandatory_evidence_issues)

    # Check 2: Overall evidence coverage
    if competencies:
        total_coverage = sum(c.get("evidence_coverage", 0.0) for c in competencies)
        avg_evidence_coverage = total_coverage / len(competencies)
        total_confidence = sum(c.get("evidence_confidence", 0.0) or 0.0 for c in competencies)
        avg_evidence_confidence = total_confidence / len(competencies)

        if avg_evidence_coverage < 0.4:
            reasons.append(f"Overall evidence coverage is low ({avg_evidence_coverage:.0%})")
            reason_codes.append("LOW_OVERALL_EVIDENCE_COVERAGE")
            risk_factors.append("low_overall_coverage")

        if avg_evidence_confidence < 0.4:
            reasons.append(f"Overall evidence confidence is low ({avg_evidence_confidence:.0%})")
            reason_codes.append("LOW_OVERALL_EVIDENCE_CONFIDENCE")
            risk_factors.append("low_overall_confidence")

    # Check 3: Evidence conflicts
    # Simplified conflict detection - in practice would be more sophisticated
    supports_count = sum(1 for e in evidence_records if e.get("supports", False))
    contradicts_count = sum(1 for e in evidence_records if not e.get("supports", True))
    total_evidence = len(evidence_records)

    if total_evidence > 0:
        conflict_ratio = contradicts_count / total_evidence
        if conflict_ratio > 0.3:  # More than 30% contradiction
            reasons.append(f"High evidence conflict detected ({conflict_ratio:.0%} contradicting evidence)")
            reason_codes.append("HIGH_EVIDENCE_CONFLICT")
            risk_factors.append("high_conflict")
        elif conflict_ratio > 0.1:  # More than 10% contradiction
            reasons.append(f"Some evidence conflict detected ({conflict_ratio:.0%} contradicting evidence)")
            reason_codes.append("SOME_EVIDENCE_CONFLICT")
            risk_factors.append("some_conflict")

    # Check 4: Missing practical evidence for mandatory NOS
    practical_evidence_count = sum(
        1 for e in evidence_records
        if e.get("source", "").upper() in ["PRACTICAL", "OBSERVED", "ASSESSED"]
    )
    if mandatory_nos and practical_evidence_count == 0:
        reasons.append("No practical/observed evidence for mandatory competencies")
        reason_codes.append("NO_PRACTICAL_EVIDENCE")
        risk_factors.append("no_practical_evidence")

    # Determine final decision based on risk factors
    # Decision logic:
    # - ABSTAIN: Critical issues with mandatory NOS
    # - NEEDS_MORE_EVIDENCE: Significant evidence gaps but no critical mandatory issues
    # - READY_FOR_ASSESSOR: Sufficient evidence with minor concerns
    # - CONFLICT_REVIEW: Significant evidence conflicts requiring review

    has_critical_mandatory_issue = any(
        "MANDATORY_EVIDENCE_MISSING" in rc or "HIGH_COMPETENCY_LOW_EVIDENCE" in rc
        for rc in reason_codes
    )

    has_high_conflict = "HIGH_EVIDENCE_CONFLICT" in reason_codes
    has_low_overall_evidence = "LOW_OVERALL_EVIDENCE_COVERAGE" in reason_codes

    # Calculate confidence in decision (inverse of uncertainty)
    uncertainty_factors = len(reason_codes)
    max_expected_factors = 5  # Arbitrary scaling factor
    confidence = max(0.1, 1.0 - (uncertainty_factors / max_expected_factors))

    # Decision logic
    if has_critical_mandatory_issue:
        status = "ABSTAIN"
        recommended_action = "HUMAN_REVIEW_REQUIRED"
        if not reasons:
            reasons.append("Critical evidence gaps in mandatory competencies prevent confident recommendation")
    elif has_high_conflict:
        status = "CONFLICT_REVIEW"
        recommended_action = "RESOLVE_EVIDENCE_CONFLICTS"
        if not reasons:
            reasons.append("Conflicting evidence requires human review before proceeding")
    elif has_low_overall_evidence or len(reason_codes) > 2:
        status = "NEEDS_MORE_EVIDENCE"
        recommended_action = "RUN_TARGETED_ASSESSMENT"
        # Suggest a specific task if we can identify gaps
        if mandatory_nos:
            # Recommend task for first mandatory NOS with gap
            for nos in mandatory_nos:
                if nos.get("evidence_coverage", 0.0) < 0.5:
                    # In a real system, we'd map NOS to task IDs
                    # For demo, we'll use a placeholder
                    next_task_id = f"TASK_{nos.get('nos_id', 'UNKNOWN')}_01"
                    break
            else:
                next_task_id = None
        else:
            next_task_id = None
    else:
        status = "READY_FOR_ASSESSOR"
        recommended_action = "PROCEED_WITH_ASSESSOR_REVIEW"
        next_task_id = None

    # Add positive factors if present
    if not reason_codes:
        strengths = []
        if mandatory_nos:
            strong_mandatory = [n for n in mandatory_nos if n.get("evidence_coverage", 0.0) >= 0.7]
            if strong_mandatory:
                strengths.append(f"{len(strong_mandatory)} mandatory NOS with strong evidence")
        if strengths:
            reasons.extend(strengths)

    # Prepare metadata
    metadata = {
        "worker_id": worker_id,
        "total_competencies": len(competencies),
        "mandatory_competencies": len(mandatory_nos),
        "evidence_records_count": len(evidence_records),
        "assessment_results_count": len(assessment_task_results),
        "assessor_observations_count": len(assessor_observations),
        "risk_factors": risk_factors,
        "strength_factors": strength_factors,
    }

    return AbstentionDecision(
        status=status,
        confidence=confidence,
        reason_codes=list(set(reason_codes)),  # Remove duplicates
        reasons=reasons,
        recommended_action=recommended_action,
        next_task_id=next_task_id,
        metadata=metadata,
    )


def should_abstain(
    competencies: List[Dict[str, Any]],
    threshold_evidence_coverage: float = 0.4,
    threshold_evidence_confidence: float = 0.4,
) -> Tuple[bool, List[str]]:
    """
    Simple helper to determine if abstention is warranted based on thresholds.

    Args:
        competencies: List of competency dictionaries
        threshold_evidence_coverage: Minimum acceptable evidence coverage
        threshold_evidence_confidence: Minimum acceptable evidence confidence

    Returns:
        Tuple of (should_abstain_bool, list_of_reasons)
    """
    reasons = []
    should_abstain_flag = False

    for nos in competencies:
        if not nos.get("mandatory", False):
            continue  # Only check mandatory NOS for abstention

        nos_id = nos.get("nos_id", "unknown")
        evidence_coverage = nos.get("evidence_coverage", 0.0)
        evidence_confidence = nos.get("evidence_confidence", 0.0) or 0.0
        competency_score = nos.get("competency_score", 0)

        # Abstain if mandatory NOS has insufficient evidence
        if evidence_coverage < threshold_evidence_coverage:
            should_abstain_flag = True
            reasons.append(
                f"Mandatory NOS {nos_id} evidence coverage ({evidence_coverage:.0%}) "
                f"below threshold ({threshold_evidence_coverage:.0%})"
            )

        # Abstain if high competency but low evidence (dangerous combination)
        if competency_score >= 70 and evidence_confidence < threshold_evidence_confidence:
            should_abstain_flag = True
            reasons.append(
                f"Mandatory NOS {nos_id} shows high competency ({competency_score}) "
                f"but low evidence confidence ({evidence_confidence:.0%})"
            )

    return should_abstain_flag, reasons