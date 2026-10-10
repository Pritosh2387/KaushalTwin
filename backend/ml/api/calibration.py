"""
KaushalTwin ML Service — API: Assessor Calibration + Consistency (Module 8)
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ml.services.calibration_service import CalibrationService
from ml.schemas.calibration import (
    AssessorScoresRequest,
    CalibrationResultResponse,
    SingleAssessorProfileRequest,
    AssessorAgreementRequest,
    AssessorProfileOutput,
)

router = APIRouter(prefix="/calibration", tags=["Assessor Calibration & Consistency"])


@router.post(
    "/analyze",
    response_model=CalibrationResultResponse,
    summary="Analyze assessor calibration and consistency",
)
def analyze_assessor_calibration(request: AssessorScoresRequest) -> CalibrationResultResponse:
    """
    Analyze assessor calibration and consistency across multiple assessors.

    This implements Module 8: Assessor Calibration + Consistency.
    Helps assessors score candidates consistently by identifying scoring differences.
    """
    try:
        result = CalibrationService.calculate_assessor_calibration(
            assessor_scores=[score.model_dump() for score in request.assessor_scores],
            competency_areas=request.competency_areas,
        )
        return CalibrationResultResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "CALIBRATION_ANALYSIS_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/assessor-profile",
    response_model=AssessorProfileOutput,
    summary="Get calibration profile for a specific assessor",
)
def get_assessor_profile(request: SingleAssessorProfileRequest) -> AssessorProfileOutput:
    """
    Get calibration profile for a specific assessor.

    Useful for individual assessor feedback and development.
    """
    try:
        profile = CalibrationService.get_assessor_profile(
            assessor_scores=[score.model_dump() for score in request.assessor_scores],
            assessor_id=request.assessor_id,
        )
        if profile is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "ASSESSOR_NOT_FOUND", "message": f"Assessor {request.assessor_id} not found in data"}}
            )
        return AssessorProfileOutput(**profile)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ASSESSOR_PROFILE_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/agreement",
    summary="Calculate agreement between two assessors",
)
def calculate_assessor_agreement(request: AssessorAgreementRequest) -> dict:
    """
    Calculate agreement metrics between two specific assessors.

    Useful for pairwise assessor comparison and inter-rater reliability.
    """
    try:
        result = CalibrationService.calculate_agreement_between_assessors(
            assessor_a_scores=[score.model_dump() for score in request.assessor_a_scores],
            assessor_b_scores=[score.model_dump() for score in request.assessor_b_scores],
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "ASSESSOR_AGREEMENT_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/case-comparison",
    summary="Compare assessor scores on specific cases",
)
def compare_assessor_cases(
    assessor_scores: List[dict],
    case_worker_ids: List[str],
) -> dict:
    """
    Compare how different assessors scored the same workers/cases.

    Helpful for identifying specific cases where assessors disagree.
    """
    try:
        # Use the main calibration analysis but focus on specific workers
        result = CalibrationService.calculate_assessor_calibration(
            assessor_scores=assessor_scores,
        )

        # Add case-specific comparison data
        case_comparison = {}
        for worker_id in case_worker_ids:
            worker_scores = [
                {
                    "assessor_id": record.get("assessor_id"),
                    "score": record.get("score"),
                }
                for record in assessor_scores
                if record.get("worker_id") == worker_id
            ]
            if worker_scores:
                scores = [s["score"] for s in worker_scores if s["score"] is not None]
                if scores:
                    case_comparison[worker_id] = {
                        "mean_score": sum(scores) / len(scores),
                        "score_range": max(scores) - min(scores) if len(scores) > 1 else 0,
                        "assessor_count": len(scores),
                        "scores": [
                            {"assessor_id": s["assessor_id"], "score": s["score"]}
                            for s in worker_scores
                        ],
                    }

        result["case_comparison"] = case_comparison
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "CASE_COMPARISON_ERROR", "message": str(exc)}}
        ) from exc