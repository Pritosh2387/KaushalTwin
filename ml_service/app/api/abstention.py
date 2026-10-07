"""
KaushalTwin ML Service — API: Abstention / Evidence Sufficiency Engine (Module 7)
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.abstention_service import AbstentionService
from app.schemas.abstention import (
    AbstentionRequest,
    AbstentionResponse,
    ShouldAbstainRequest,
    ShouldAbstainResponse,
    AbstentionReasonsResponse,
)

router = APIRouter(prefix="/abstention", tags=["Abstention & Evidence Sufficiency"])


@router.post(
    "/check",
    response_model=AbstentionResponse,
    summary="Check evidence sufficiency and determine if abstention is warranted",
)
def check_evidence_sufficiency(request: AbstentionRequest) -> AbstentionResponse:
    """
    Determine if there is sufficient evidence to proceed with assessment recommendation.

    This implements Module 7: Abstention / Evidence Sufficiency Engine.
    The AI can say "INSUFFICIENT EVIDENCE" instead of pretending to know.
    """
    try:
        result = AbstentionService.check_evidence_sufficiency(
            worker_id=request.worker_id,
            competencies=request.competencies,
            evidence_records=request.evidence_records,
            assessment_task_results=request.assessment_task_results,
            assessor_observations=request.assessor_observations,
        )
        return AbstentionResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ABSTENTION_CHECK_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/decision",
    response_model=ShouldAbstainResponse,
    summary="Get simple yes/no abstention decision based on thresholds",
)
def get_abstention_decision(request: ShouldAbstainRequest) -> ShouldAbstainResponse:
    """
    Get a simple abstention decision based on configurable thresholds.

    Useful for quick checks during assessment workflow.
    """
    try:
        result = AbstentionService.should_abstain(
            competencies=request.competencies,
            threshold_evidence_coverage=request.threshold_evidence_coverage,
            threshold_evidence_confidence=request.threshold_evidence_confidence,
        )
        return ShouldAbstainResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ABSTENTION_DECISION_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/reasons",
    response_model=AbstentionReasonsResponse,
    summary="Get human-readable reasons for potential abstention",
)
def get_abstention_reasons(
    worker_id: str,
    competencies: List[dict],
    evidence_records: Optional[List[dict]] = None,
) -> AbstentionReasonsResponse:
    """
    Get explanations for why the system might abstain from making a recommendation.

    Helpful for assessor feedback and transparency.
    """
    try:
        reasons = AbstentionService.get_abstention_reasons(
            competencies=competencies,
            evidence_records=evidence_records,
        )
        return AbstentionReasonsResponse(
            worker_id=worker_id,
            reasons=reasons,
            total_competencies=len(competencies),
            mandatory_competniques=len([c for c in competencies if c.get("mandatory", False)]),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ABSTENTION_REASONS_ERROR", "message": str(exc)}}
        ) from exc