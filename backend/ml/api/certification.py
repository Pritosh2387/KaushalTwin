"""
KaushalTwin ML Service — API: Competency Profile + Certification Recommendation (Module 9)
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ml.services.certification_service import CertificationService
from ml.schemas.certification import (
    CertificationRecommendationRequest,
    CertificationRecommendationResponse,
    CompetencyProfileSummaryResponse,
)

router = APIRouter(prefix="/certification", tags=["Certification Recommendation"])


@router.post(
    "/recommend",
    response_model=CertificationRecommendationResponse,
    summary="Generate certification recommendation based on competency profile",
)
def make_certification_recommendation(request: CertificationRecommendationRequest) -> CertificationRecommendationResponse:
    """
    Generate a certification recommendation based on all available information.

    This implements Module 9: Competency Profile + Certification Recommendation.
    The system generates CERTIFICATION RECOMMENDATION only - final decision rests with human assessor.
    """
    try:
        result = CertificationService.make_certification_recommendation(
            worker_id=request.worker_id,
            competency_profile=request.competency_profile,
            skill_gap_analysis=request.skill_gap_analysis,
            abstention_decision=request.abstention_decision,
            calibration_info=request.calibration_info,
        )
        return CertificationRecommendationResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "CERTIFICATION_RECOMMENDATION_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/profile-summary",
    response_model=CompetencyProfileSummaryResponse,
    summary="Get summary of competency profile",
)
def get_competency_profile_summary(
    worker_id: str,
    competency_profile: List[dict],
) -> CompetencyProfileSummaryResponse:
    """
    Get a summary of the competency profile for dashboard display.

    Useful for quick overview of worker's competency status.
    """
    try:
        summary = CertificationService.get_competency_profile_summary(competency_profile)
        return CompetencyProfileSummaryResponse(
            worker_id=worker_id,
            **summary
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "PROFILE_SUMMARY_ERROR", "message": str(exc)}}
        ) from exc