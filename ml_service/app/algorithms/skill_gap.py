"""
KaushalTwin ML Service — Algorithm: Skill Gap + Evidence Debt (Module 6)
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NOSGapAnalysis:
    """Analysis of a single NOS competency gap."""
    nos_id: str
    mandatory: bool
    competency_score: int  # 0-100
    evidence_confidence: float  # 0.0-1.0
    evidence_coverage: float  # 0.0-1.0
    evidence_debt: float  # 0.0-1.0 (1 - evidence_coverage)
    missing_evidence: List[str]
    supporting_evidence: List[str]
    status: str  # "STRONG", "WEAK", "MISSING"
    reason: str


def calculate_skill_gap(
    nos_id: str,
    competency_score: int,
    evidence_confidence: float,
    evidence_coverage: float,
    mandatory: bool = False,
    supporting_evidence: Optional[List[str]] = None,
    missing_evidence: Optional[List[str]] = None,
) -> NOSGapAnalysis:
    """
    Calculate skill gap and evidence debt for a single NOS.

    Args:
        nos_id: NOS identifier
        competency_score: Competency score (0-100)
        evidence_confidence: Confidence in evidence (0.0-1.0)
        evidence_coverage: Coverage of evidence (0.0-1.0)
        mandatory: Whether this NOS is mandatory
        supporting_evidence: List of supporting evidence items
        missing_evidence: List of missing evidence items

    Returns:
        NOSGapAnalysis object with calculated fields
    """
    if supporting_evidence is None:
        supporting_evidence = []
    if missing_evidence is None:
        missing_evidence = []

    # Calculate evidence debt (can be customized later)
    evidence_debt = 1.0 - evidence_coverage

    # Determine status based on competency and evidence
    if competency_score >= 80 and evidence_confidence >= 0.8 and evidence_coverage >= 0.8:
        status = "STRONG"
        reason = "High competency with strong evidence coverage"
    elif competency_score >= 60 and evidence_confidence >= 0.5 and evidence_coverage >= 0.5:
        status = "WEAK"
        reason = "Moderate competency with some evidence gaps"
    else:
        status = "MISSING"
        reason = "Low competency or insufficient evidence"

    # Override for mandatory NOS with low evidence
    if mandatory and evidence_coverage < 0.5:
        status = "MISSING"
        reason = f"Mandatory NOS {nos_id} has insufficient evidence coverage"

    return NOSGapAnalysis(
        nos_id=nos_id,
        mandatory=mandatory,
        competency_score=competency_score,
        evidence_confidence=evidence_confidence,
        evidence_coverage=evidence_coverage,
        evidence_debt=evidence_debt,
        missing_evidence=missing_evidence,
        supporting_evidence=supporting_evidence,
        status=status,
        reason=reason,
    )


def analyze_skill_gaps(
    worker_id: str,
    competencies: List[Dict[str, Any]],
    evidence_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Analyze skill gaps across all NOS competencies for a worker.

    Args:
        worker_id: Worker identifier
        competencies: List of competency dictionaries from competency twin
        evidence_records: List of evidence records (optional)

    Returns:
        Dictionary containing overall evidence coverage/debt and gaps per NOS
    """
    if evidence_records is None:
        evidence_records = []

    # Extract evidence by NOS ID for easier lookup
    evidence_by_nos: Dict[str, List[Dict[str, Any]]] = {}
    for evidence in evidence_records:
        # Assuming evidence has a 'nos_id' field or similar
        # For demo purposes, we'll distribute evidence evenly or based on simple matching
        nos_id = evidence.get("nos_id", "unknown")
        if nos_id not in evidence_by_nos:
            evidence_by_nos[nos_id] = []
        evidence_by_nos[nos_id].append(evidence)

    gaps = []
    total_evidence_coverage = 0.0
    total_evidence_confidence = 0.0
    assessed_nos_count = 0

    for comp in competencies:
        nos_id = comp.get("nos_id")
        if not nos_id:
            continue

        competency_score = comp.get("competency_score", 0)
        evidence_confidence = comp.get("evidence_confidence", 0.0) or 0.0
        evidence_coverage = comp.get("evidence_coverage", 0.0)
        mandatory = comp.get("mandatory", False)

        # Get evidence for this NOS
        nos_evidence = evidence_by_nos.get(nos_id, [])

        # Extract supporting and missing evidence from evidence records
        supporting = [e.get("notes", "") for e in nos_evidence if e.get("supports", False)]
        missing = [e.get("notes", "") for e in nos_evidence if not e.get("supports", True)]

        # Clean up empty strings
        supporting = [s for s in supporting if s.strip()]
        missing = [m for m in missing if m.strip()]

        # If no specific evidence provided, generate demo evidence based on coverage
        if not supporting and not missing:
            if evidence_coverage >= 0.8:
                supporting = ["Practical observation completed", "Assessor validation"]
                missing = []
            elif evidence_coverage >= 0.5:
                supporting = ["Self-declaration supported by some documentation"]
                missing = ["Practical observation needed", "Assessor verification"]
            else:
                supporting = ["Self-declaration only"]
                missing = [
                    "Practical observation required",
                    "Assessor validation needed",
                    "Documentation of competency"
                ]

        gap_analysis = calculate_skill_gap(
            nos_id=nos_id,
            competency_score=competency_score,
            evidence_confidence=evidence_confidence,
            evidence_coverage=evidence_coverage,
            mandatory=mandatory,
            supporting_evidence=supporting,
            missing_evidence=missing,
        )

        gaps.append({
            "nos_id": gap_analysis.nos_id,
            "mandatory": gap_analysis.mandatory,
            "competency_score": gap_analysis.competency_score,
            "evidence_confidence": gap_analysis.evidence_confidence,
            "evidence_coverage": gap_analysis.evidence_coverage,
            "evidence_debt": gap_analysis.evidence_debt,
            "missing_evidence": gap_analysis.missing_evidence,
            "supporting_evidence": gap_analysis.supporting_evidence,
            "status": gap_analysis.status,
            "reason": gap_analysis.reason,
        })

        # Accumulate for overall calculations
        if evidence_coverage > 0:  # Only count NOS with some evidence
            total_evidence_coverage += evidence_coverage
            total_evidence_confidence += evidence_confidence
            assessed_nos_count += 1

    # Calculate overall evidence coverage and debt
    overall_evidence_coverage = (
        total_evidence_coverage / assessed_nos_count if assessed_nos_count > 0 else 0.0
    )
    overall_evidence_debt = 1.0 - overall_evidence_coverage

    return {
        "worker_id": worker_id,
        "overall_evidence_coverage": overall_evidence_coverage,
        "overall_evidence_debt": overall_evidence_debt,
        "gaps": gaps,
        "summary": {
            "total_nos_assessed": len([g for g in gaps if g["evidence_coverage"] > 0]),
            "total_nos_mandatory": len([g for g in gaps if g["mandatory"]]),
            "strong_areas": len([g for g in gaps if g["status"] == "STRONG"]),
            "weak_areas": len([g for g in gaps if g["status"] == "WEAK"]),
            "missing_areas": len([g for g in gaps if g["status"] == "MISSING"]),
        }
    }