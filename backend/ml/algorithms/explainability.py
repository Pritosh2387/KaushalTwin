"""
KaushalTwin ML Service — Algorithm: Explainability + Audit Trail + Decision Report (Module 10)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ProvenanceType(str, Enum):
    """Provenance types for evidence and claims."""
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    ASSESSED = "ASSESSED"
    INFERRED = "INFERRED"
    DERIVED = "DERIVED"


@dataclass
class EvidenceWithProvenance:
    """Evidence item with provenance tracking."""
    type: ProvenanceType
    description: str
    strength: float  # 0.0-1.0, how strong this evidence is
    importance: float = 1.0  # How important this evidence is to the claim


@dataclass
class ExplainableClaim:
    """A claim that can be explained with provenance tracking."""
    claim: str
    status: str  # e.g., "SUPPORTED", "REFUTED", "INSUFFICIENT_EVIDENCE"
    supporting_evidence: List[EvidenceWithProvenance]
    missing_evidence: List[EvidenceWithProvenance]
    explanation_summary: str


def explain_claim(
    claim: str,
    worker_declaration: Optional[str] = None,
    observed_evidence: Optional[List[Dict[str, Any]]] = None,
    assessed_evidence: Optional[List[Dict[str, Any]]] = None,
    inferred_evidence: Optional[List[Dict[str, Any]]] = None,
    derived_evidence: Optional[List[Dict[str, Any]]] = None,
) -> ExplainableClaim:
    """
    Explain a claim with provenance tracking.

    Implements Part A of Module 10: Explainability.
    Tracks what was declared, observed, assessed, inferred, and derived.

    Args:
        claim: The claim being evaluated (e.g., "Worker can perform safe isolation")
        worker_declaration: What the worker declared about this claim
        observed_evidence: Evidence from direct observation
        assessed_evidence: Evidence from assessor evaluation
        inferred_evidence: Evidence inferred from other facts
        derived_evidence: Evidence derived through calculations/algorithms

    Returns:
        ExplainableClaim with provenance-tracked evidence
    """
    if observed_evidence is None:
        observed_evidence = []
    if assessed_evidence is None:
        assessed_evidence = []
    if inferred_evidence is None:
        inferred_evidence = []
    if derived_evidence is None:
        derived_evidence = []

    supporting_evidence = []
    missing_evidence = []

    # Process worker declaration (DECLARED)
    if worker_declaration:
        # In a real system, we'd analyze the declaration for relevance
        # For now, we'll treat any non-empty declaration as supporting evidence
        supporting_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.DECLARED,
                description=worker_declaration or "Worker declaration",
                strength=0.3,  # Declarations are weak evidence
                importance=0.5,
            )
        )
    else:
        # No declaration is missing evidence
        missing_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.DECLARED,
                description="Worker declaration about competency",
                strength=0.0,
                importance=0.5,
            )
        )

    # Process observed evidence (OBSERVED)
    for evidence in observed_evidence:
        supporting_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.OBSERVED,
                description=evidence.get("description", "Observed evidence"),
                strength=evidence.get("strength", 0.9),
                importance=evidence.get("importance", 1.0),
            )
        )

    # If we have no observed evidence but the claim requires it, mark as missing
    if not observed_evidence and _claim_requires_observation(claim):
        missing_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.OBSERVED,
                description="Direct observation of competency",
                strength=0.0,
                importance=1.0,  # Critical for many competencies
            )
        )

    # Process assessed evidence (ASSESSED)
    for evidence in assessed_evidence:
        supporting_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.ASSESSED,
                description=evidence.get("description", "Assessor evaluation"),
                strength=evidence.get("strength", 0.8),
                importance=evidence.get("importance", 1.0),
            )
        )

    # Process inferred evidence (INFERRED)
    for evidence in inferred_evidence:
        supporting_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.INFERRED,
                description=evidence.get("description", "Inferred from other evidence"),
                strength=evidence.get("strength", 0.6),
                importance=evidence.get("importance", 0.7),
            )
        )

    # Process derived evidence (DERIVED)
    for evidence in derived_evidence:
        supporting_evidence.append(
            EvidenceWithProvenance(
                type=ProvenanceType.DERIVED,
                description=evidence.get("description", "Derived through calculation"),
                strength=evidence.get("strength", 0.7),
                importance=evidence.get("importance", 0.8),
            )
        )

    # Determine claim status based on evidence balance
    status, explanation_summary = _determine_claim_status(
        supporting_evidence, missing_evidence, claim
    )

    return ExplainableClaim(
        claim=claim,
        status=status,
        supporting_evidence=supporting_evidence,
        missing_evidence=missing_evidence,
        explanation_summary=explanation_summary,
    )


def _claim_requires_observation(claim: str) -> bool:
    """
    Determine if a claim requires direct observation for validation.
    """
    observation_keywords = [
        "perform", "demonstrate", "show", "execute", "carry out",
        "safe isolation", "fault finding", "install", "test",
        "practical", "hands-on", "direct"
    ]
    claim_lower = claim.lower()
    return any(keyword in claim_lower for keyword in observation_keywords)


def _determine_claim_status(
    supporting_evidence: List[EvidenceWithProvenance],
    missing_evidence: List[EvidenceWithProvenance],
    claim: str,
) -> tuple[str, str]:
    """
    Determine the status of a claim based on evidence balance.
    """
    # Calculate weighted support score
    total_support = sum(
        e.strength * e.importance for e in supporting_evidence
    )
    max_possible_support = sum(
        e.importance for e in supporting_evidence
    ) + sum(
        e.importance for e in missing_evidence if e.importance > 0
    )

    if max_possible_support == 0:
        support_ratio = 0.0
    else:
        support_ratio = total_support / max_possible_support

    # Check for critical missing evidence (high importance, zero strength)
    critical_missing = [
        e for e in missing_evidence
        if e.importance >= 0.8 and e.strength == 0.0
    ]

    # Determine status
    if len(critical_missing) > 0:
        status = "INSUFFICIENT_EVIDENCE"
        explanation = f"Critical missing evidence: {len(critical_missing)} items requiring direct observation or verification"
    elif support_ratio >= 0.8:
        status = "SUPPORTED"
        explanation = f"Strong evidence supports the claim ({support_ratio:.0%} support)"
    elif support_ratio >= 0.6:
        status = "PARTIALLY_SUPPORTED"
        explanation = f"Moderate evidence supports the claim ({support_ratio:.0%} support)"
    elif support_ratio >= 0.3:
        status = "WEAKLY_SUPPORTED"
        explanation = f"Limited evidence supports the claim ({support_ratio:.0%} support)"
    else:
        status = "INSUFFICIENT_EVIDENCE"
        explanation = f"Insufficient evidence to support the claim ({support_ratio:.0%} support)"

    return status, explanation


def generate_audit_event(
    worker_id: str,
    action: str,
    module: str,
    input_summary: Dict[str, Any],
    output_summary: Dict[str, Any],
    assessor_id: Optional[str] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    evidence_references: Optional[List[str]] = None,
    model_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate an audit record for tracking decisions and actions.

    Implements Part B of Module 10: Audit Trail.
    Creates a deterministic audit record that can be verified.

    Args:
        worker_id: Worker being assessed
        action: Action taken (e.g., "skill_gap_analysis", "certification_recommendation")
        module: Module name (e.g., "skill_gap", "certification")
        input_summary: Summary of inputs to the action
        output_summary: Summary of outputs from the action
        assessor_id: Assessor ID if applicable
        previous_state: State before action (if applicable)
        new_state: State after action (if applicable)
        evidence_references: References to evidence used
        model_info: Information about models/methods used

    Returns:
        Dictionary representing the audit event
    """
    import hashlib
    import json
    from datetime import datetime

    # Create a deterministic JSON representation
    audit_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "worker_id": worker_id,
        "assessor_id": assessor_id,
        "action": action,
        "module": module,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "previous_state": previous_state,
        "new_state": new_state,
        "evidence_references": evidence_references or [],
        "model_info": model_info or {
            "method": "rule_based_algorithms",
            "version": "1.0",
            "note": "Deterministic algorithms used for transparency"
        },
    }

    # Remove None values to keep output clean
    audit_data = {k: v for k, v in audit_data.items() if v is not None}

    # Create a deterministic JSON string for hashing
    json_string = json.dumps(audit_data, sort_keys=True, separators=(',', ':'))

    # Calculate SHA-256 hash
    audit_hash = hashlib.sha256(json_string.encode('utf-8')).hexdigest()

    # Add hash to the audit data
    audit_data["hash"] = audit_hash
    audit_data["hash_algorithm"] = "SHA-256"

    return audit_data


def verify_audit_event(audit_event: Dict[str, Any]) -> bool:
    """
    Verify the integrity of an audit event by checking its hash.

    Args:
        audit_event: Audit event dictionary to verify

    Returns:
        True if audit event is valid, False otherwise
    """
    import hashlib
    import json

    # Make a copy without the hash for verification
    audit_copy = audit_event.copy()
    provided_hash = audit_copy.pop("hash", None)
    audit_copy.pop("hash_algorithm", None)  # Remove hash algorithm too

    if provided_hash is None:
        return False

    # Create deterministic JSON string
    json_string = json.dumps(audit_copy, sort_keys=True, separators=(',', ':'))

    # Calculate expected hash
    expected_hash = hashlib.sha256(json_string.encode('utf-8')).hexdigest()

    return provided_hash == expected_hash


def generate_decision_report(
    worker_id: str,
    worker_info: Dict[str, Any],
    skills_extracted: List[Dict[str, Any]],
    nos_mapping: List[Dict[str, Any]],
    competency_profile: List[Dict[str, Any]],
    evidence_summary: Dict[str, Any],
    skill_gaps: List[Dict[str, Any]],
    assessment_summary: Dict[str, Any],
    abstention_result: Dict[str, Any],
    calibration_info: Optional[Dict[str, Any]] = None,
    certification_recommendation: Optional[Dict[str, Any]] = None,
    explanation: Optional[Dict[str, Any]] = None,
    audit_event: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive decision report for assessors.

    Implements Part C of Module 10: Decision Report.
    Combines all outputs into a single assessor-facing report.

    Args:
        worker_id: Worker identifier
        worker_info: Basic worker information
        skills_extracted: Results from skill extraction
        nos_mapping: Results from NOS mapping
        competency_profile: Results from competency scoring
        evidence_summary: Summary of evidence analysis
        skill_gaps: Results from skill gap analysis
        assessment_summary: Summary of assessment tasks completed
        abstention_result: Results from evidence sufficiency check
        calibration_info: Results from assessor calibration (optional)
        certification_recommendation: Results from certification recommendation (optional)
        explanation: Explainability analysis (optional)
        audit_event: Audit trail information (optional)

    Returns:
        Comprehensive decision report for assessor review
    """
    report = {
        "worker": worker_info,
        "skills": skills_extracted,
        "nos_mapping": nos_mapping,
        "competency_profile": competency_profile,
        "evidence_summary": evidence_summary,
        "skill_gaps": skill_gaps,
        "assessment_summary": assessment_summary,
        "abstention": abstention_result,
    }

    if calibration_info is not None:
        report["calibration"] = calibration_info

    if certification_recommendation is not None:
        report["recommendation"] = certification_recommendation

    if explanation is not None:
        report["explanation"] = explanation

    if audit_event is not None:
        report["audit"] = audit_event

    # Add metadata
    report["metadata"] = {
        "report_version": "1.0",
        "generated_at": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "report_type": "comprehensive_assessor_report",
        "ai_authority": "RECOMMENDATION_ONLY",
        "assessor_action_required": True,
    }

    return report