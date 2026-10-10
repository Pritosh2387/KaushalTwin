"""
KaushalTwin Backend — Pydantic Schemas: ML integration, Decisions, Reports
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ── ML Analysis Request ───────────────────────────────────────────────────────

class MLAnalysisRequest(BaseModel):
    """Request body to trigger a full ML pipeline run for an assessment."""
    language: str = Field("en", description="BCP-47 language code")
    include_calibration: bool = Field(False)
    claim_for_explanation: Optional[str] = None


class AIRunResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    worker_id: uuid.UUID
    run_status: str
    recommendation: Optional[str]
    ml_response: Optional[Any]  # Full ML response parsed as dict
    error_detail: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class NextTaskRecommendationResponse(BaseModel):
    """Response for the next-best-task recommendation endpoint."""
    ai_run_id: uuid.UUID
    task_id: Optional[uuid.UUID]  # Persisted AssessmentTask id if a task was recommended
    selected_task: Optional[dict]  # From ML service
    priority_score: float
    reason: list[str]
    alternatives: list[dict]
    note: str


# ── Decision ─────────────────────────────────────────────────────────────────

class DecisionRequest(BaseModel):
    action: str = Field(
        ...,
        description="ACCEPT_RECOMMENDATION | REJECT_RECOMMENDATION | "
                    "REQUEST_MORE_EVIDENCE | MODIFY_RECOMMENDATION",
    )
    ai_run_id: Optional[uuid.UUID] = None
    comments: Optional[str] = None
    modified_recommendation: Optional[str] = None


class DecisionResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    assessor_id: uuid.UUID
    action: str
    comments: Optional[str]
    modified_recommendation: Optional[str]
    ai_run_id: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Report ───────────────────────────────────────────────────────────────────

class AssessmentReport(BaseModel):
    """Structured JSON report for an assessment."""
    generated_at: datetime
    worker: dict
    assessment: dict
    evidence_summary: dict
    ai_runs: list[dict]
    tasks: list[dict]
    latest_recommendation: Optional[dict]
    latest_decision: Optional[dict]
    audit_timeline: list[dict]
    note: str = (
        "AI recommendations are advisory only. "
        "The final decision rests with the human assessor."
    )
