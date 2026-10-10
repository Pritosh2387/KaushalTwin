"""
KaushalTwin ML Service — Competency API
Module 3: Competency Twin & Competency Scoring
"""

from fastapi import APIRouter, HTTPException
from ml.schemas.competency import (
    CompetencyScoreRequest,
    CompetencyScoreResponse,
    CompetencyTwinRequest,
    CompetencyTwinResponse,
    ScoringDetail,
    CompetencySummary,
)
from ml.services.competency_service import score_competency, build_competency_twin

router = APIRouter(prefix="/competency", tags=["Module 3 · Competency Twin"])


@router.post(
    "/score",
    response_model=CompetencyScoreResponse,
    summary="Calculate competency score for one NOS element",
)
def score_competency_endpoint(request: CompetencyScoreRequest) -> CompetencyScoreResponse:
    """
    Calculate the weighted competency score for a single NOS element.

    - competency_score: transparent weighted criterion score (0-100)
    - evidence_confidence: null until the future confidence engine (Module 7)
    - evidence_coverage: fraction of criteria that have been observed
    """
    try:
        criteria_raw = [c.model_dump() for c in request.criteria]
        result = score_competency(
            nos_id=request.nos_id,
            criteria=criteria_raw,
            mandatory=request.mandatory,
            importance=request.importance,
            evidence_confidence=request.evidence_confidence,
            required_criteria_ids=request.required_criteria_ids,
        )
        return CompetencyScoreResponse(
            nos_id=result["nos_id"],
            competency_score=result["competency_score"],
            evidence_confidence=result["evidence_confidence"],
            evidence_coverage=result["evidence_coverage"],
            mandatory=result["mandatory"],
            importance=result["importance"],
            status=result["status"],
            scoring_detail=ScoringDetail(**result["scoring_detail"]),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "SCORING_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/twin",
    response_model=CompetencyTwinResponse,
    summary="Build a Competency Twin for a worker across multiple NOS elements",
)
def build_twin_endpoint(request: CompetencyTwinRequest) -> CompetencyTwinResponse:
    """
    Build a lightweight Competency Twin from multi-NOS assessment data.

    No database required — stateless JSON in/out.
    The main backend persists and updates these states.
    """
    try:
        comps_raw = [c.model_dump() for c in request.competencies]
        result = build_competency_twin(
            worker_id=request.worker_id,
            competencies_input=comps_raw,
        )
        return CompetencyTwinResponse(
            worker_id=result["worker_id"],
            competencies=[
                CompetencyScoreResponse(
                    nos_id=c["nos_id"],
                    competency_score=c["competency_score"],
                    evidence_confidence=c["evidence_confidence"],
                    evidence_coverage=c["evidence_coverage"],
                    mandatory=c["mandatory"],
                    importance=c["importance"],
                    status=c["status"],
                    scoring_detail=ScoringDetail(**c["scoring_detail"]),
                )
                for c in result["competencies"]
            ],
            summary=CompetencySummary(**result["summary"]),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "TWIN_BUILD_ERROR", "message": str(exc)}},
        ) from exc
