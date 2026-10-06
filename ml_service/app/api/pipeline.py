"""
KaushalTwin ML Service — Unified Pipeline API
Integration endpoint: transcript → skills → NOS → competency → next task
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.preprocessing_service import preprocess_text
from app.services.skill_service import extract_skills, map_skills_to_nos
from app.services.competency_service import build_competency_twin
from app.services.evidence_service import analyse_evidence
from app.services.task_selection_service import get_next_task, rank_all_tasks
from app.algorithms.task_selector import should_continue_assessment

router = APIRouter(prefix="/pipeline", tags=["Unified Pipeline"])


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class PipelineRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)
    language: str = Field("en")
    trade: str = Field("electrician")
    transcript: str = Field(..., min_length=1)
    competencies: list[dict] = Field(
        default=[],
        description="Existing competency state (list of NOSCompetencyInput dicts). Leave empty for first run.",
    )
    evidence: list[dict] = Field(
        default=[],
        description="Evidence records for conflict analysis. Leave empty if none.",
    )
    available_tasks: Optional[list[dict]] = Field(
        None,
        description="Custom task list. If omitted, uses built-in demo tasks.",
    )
    exclude_task_ids: Optional[list[str]] = None
    top_k_nos: int = Field(3, ge=1, le=10)


class PipelineResponse(BaseModel):
    worker_id: str
    preprocessing: dict
    skills: list[dict]
    nos_candidates: list[dict]
    competency_twin: dict
    evidence_features: Optional[dict]
    next_task: Optional[dict]
    ranked_tasks: list[dict]
    continuation: dict


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/worker-assessment",
    response_model=PipelineResponse,
    summary="Run the full ML pipeline for a worker assessment session",
)
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    """
    Unified pipeline: transcript → preprocess → extract skills → map to NOS
    → build competency twin → analyse evidence → select next task.

    All steps are individually callable via their own endpoints.
    This endpoint combines them for demo and integration testing.
    """
    try:
        # Step 1: Preprocess
        pre = preprocess_text(request.transcript, language=request.language)

        # Step 2: Extract skills
        skill_result = extract_skills(
            text=pre["normalized_text"],
            language=pre["language"],
            trade=request.trade,
            provider_name="demo",
        )
        skills = skill_result["skills"]

        # Step 3: Map skills to NOS candidates
        nos_mappings = map_skills_to_nos(skills, top_k=request.top_k_nos)

        # Step 4: Build competency twin (uses provided criteria if any)
        if request.competencies:
            twin = build_competency_twin(request.worker_id, request.competencies)
        else:
            twin = {"worker_id": request.worker_id, "competencies": [], "summary": {}}

        # Step 5: Evidence features (if provided)
        ev_features = None
        if request.evidence:
            ev_features = analyse_evidence(request.evidence)

        # Step 6: Task selection
        competency_states = twin.get("competencies", [])
        next_task = get_next_task(
            competency_states,
            available_tasks=request.available_tasks,
            exclude_task_ids=request.exclude_task_ids,
        )
        ranked = rank_all_tasks(
            competency_states,
            available_tasks=request.available_tasks,
            exclude_task_ids=request.exclude_task_ids,
        )

        # Step 7: Continuation check
        continuation = should_continue_assessment(competency_states)

        return PipelineResponse(
            worker_id=request.worker_id,
            preprocessing=pre,
            skills=skills,
            nos_candidates=nos_mappings,
            competency_twin=twin,
            evidence_features=ev_features,
            next_task=next_task,
            ranked_tasks=ranked[:5],  # top 5
            continuation=continuation,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "PIPELINE_ERROR", "message": str(exc)}},
        ) from exc
