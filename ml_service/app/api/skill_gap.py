"""
KaushalTwin ML Service — API: Skill Gap + Evidence Debt (Module 6)
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.skill_gap_service import SkillGapService
from app.schemas.skill_gap import (
    SkillGapRequest,
    SkillGapResponse,
    EvidenceDebtRequest,
    EvidenceDebtResponse,
    MissingEvidenceRequest,
    MissingEvidenceResponse,
    NOSGapOutput,
)

router = APIRouter(prefix="/skill-gap", tags=["Skill Gap & Evidence Debt"])


@router.post(
    "/analyze",
    response_model=SkillGapResponse,
    summary="Analyze skill gaps and evidence debt for a worker",
)
def analyze_skill_gaps(request: SkillGapRequest) -> SkillGapResponse:
    """
    Analyze skill gaps and calculate evidence debt across all NOS competencies.

    This implements Module 6: Skill Gap + Evidence Debt.
    """
    try:
        result = SkillGapService.analyze_skill_gaps(
            worker_id=request.worker_id,
            competencies=[comp.model_dump() for comp in request.competencies],
            evidence_records=request.evidence_records,
        )
        return SkillGapResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "SKILL_GAP_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/evidence-debt",
    response_model=EvidenceDebtResponse,
    summary="Calculate evidence debt from evidence coverage",
)
def calculate_evidence_debt(request: EvidenceDebtRequest) -> EvidenceDebtResponse:
    """
    Calculate evidence debt (1 - evidence_coverage).

    Evidence debt represents the proportion of missing evidence needed
    for confident assessment.
    """
    try:
        evidence_debt = SkillGapService.calculate_evidence_debt(request.evidence_coverage)

        # Provide interpretation based on debt level
        if evidence_debt <= 0.2:
            interpretation = "Low evidence debt - strong evidence coverage"
        elif evidence_debt <= 0.5:
            interpretation = "Moderate evidence debt - some evidence gaps"
        elif evidence_debt <= 0.8:
            interpretation = "High evidence debt - significant evidence gaps"
        else:
            interpretation = "Very high evidence debt - insufficient evidence for assessment"

        return EvidenceDebtResponse(
            evidence_coverage=request.evidence_coverage,
            evidence_debt=evidence_debt,
            interpretation=interpretation,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EVIDENCE_DEBT_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/missing-evidence",
    response_model=MissingEvidenceResponse,
    summary="Identify missing evidence for a specific NOS",
)
def identify_missing_evidence(request: MissingEvidenceRequest) -> MissingEvidenceResponse:
    """
    Identify what evidence is missing for a specific NOS competency.

    Helpful for generating targeted assessment recommendations.
    """
    try:
        # Standard evidence types by importance
        evidence_type_weights = {
            "SELF_DECLARATION": 0.1,
            "PEER_VALIDATION": 0.2,
            "EMPLOYER_VERIFICATION": 0.2,
            "PRACTICAL_OBSERVATION": 0.3,
            "ASSESSOR_VALIDATION": 0.2,
            "DOCUMENTATION": 0.1,
            "TEST_RESULTS": 0.1,
        }

        # Determine required evidence based on mandatory status
        if request.mandatory:
            required_types = [
                "PRACTICAL_OBSERVATION",
                "ASSESSOR_VALIDATION",
                "DOCUMENTATION",
            ]
        else:
            required_types = list(evidence_type_weights.keys())

        # Calculate what's missing
        current_set = set(request.current_evidence)
        missing_types = [et for et in required_types if et not in current_set]

        # Simple evidence debt calculation based on missing critical evidence
        evidence_debt = 0.0
        if request.mandatory:
            # For mandatory NOS, practical observation and assessor validation are critical
            critical_missing = [
                et for et in missing_types
                if et in ["PRACTICAL_OBSERVATION", "ASSESSOR_VALIDATION"]
            ]
            evidence_debt = len(critical_missing) * 0.4  # Each critical missing adds 0.4 debt
            evidence_debt = min(1.0, evidence_debt)  # Cap at 1.0
        else:
            evidence_debt = len(missing_types) * 0.15  # Each missing type adds 0.15
            evidence_debt = min(1.0, evidence_debt)

        return MissingEvidenceResponse(
            nos_id=request.nos_id,
            mandatory=request.mandatory,
            current_evidence=request.current_evidence,
            missing_evidence=missing_types,
            required_evidence_types=required_types,
            evidence_debt=evidence_debt,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "MISSING_EVIDENCE_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/summary",
    summary="Get summary of skill gaps analysis",
)
def get_skill_gap_summary(
    worker_id: str,
    competencies: List[dict],
) -> dict:
    """
    Get a summary of skill gaps analysis (simplified endpoint).

    Useful for dashboard views.
    """
    try:
        result = SkillGapService.analyze_skill_gaps(
            worker_id=worker_id,
            competencies=competencies,
        )
        summary = SkillGapService.get_gap_summary(result["gaps"])
        return {
            "worker_id": worker_id,
            "overall_evidence_coverage": result["overall_evidence_coverage"],
            "overall_evidence_debt": result["overall_evidence_debt"],
            "summary": summary,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "SKILL_GAP_SUMMARY_ERROR", "message": str(exc)}}
        ) from exc