"""
KaushalTwin Backend — Pydantic Schemas: Assessment and Tasks
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ── Assessment ────────────────────────────────────────────────────────────────

class AssessmentCreateRequest(BaseModel):
    worker_id: uuid.UUID
    trade: str = Field(..., min_length=1, max_length=255)
    notes: Optional[str] = None


class AssessmentUpdateRequest(BaseModel):
    notes: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    assessor_id: uuid.UUID
    trade: str
    status: str
    notes: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssessmentListResponse(BaseModel):
    items: list[AssessmentResponse]
    total: int
    skip: int
    limit: int


# ── Task ─────────────────────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = None
    target_nos_id: Optional[str] = None
    selection_source: str = Field("ASSESSOR_ASSIGNED")
    evaluation_criteria: Optional[Any] = None  # JSON-serializable


class TaskResultRequest(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    assessor_comments: Optional[str] = None
    evidence_references: Optional[list[str]] = None  # list of evidence record IDs


class TaskResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    title: str
    description: Optional[str]
    target_nos_id: Optional[str]
    ml_task_id: Optional[str]
    selection_source: str
    ai_priority_score: Optional[float]
    ai_reasons: Optional[str]
    status: str
    score: Optional[float]
    assessor_comments: Optional[str]
    evidence_references: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
