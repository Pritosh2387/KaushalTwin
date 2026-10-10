"""
KaushalTwin ML Service — Pydantic Schemas: Abstention / Evidence Sufficiency (Module 7)
"""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class AbstentionRequest(BaseModel):
    """Request for abstention/evidence sufficiency check."""
    worker_id: str = Field(..., min_length=1)
    competencies: List[dict] = Field(
        ..., min_length=1,
        description="List of competency dictionaries from competency twin"
    )
    evidence_records: Optional[List[dict]] = Field(
        None,
        description="Optional evidence records for detailed analysis"
    )
    assessment_task_results: Optional[List[dict]] = Field(
        None,
        description="Results from completed assessment tasks"
    )
    assessor_observations: Optional[List[dict]] = Field(
        None,
        description="Direct observations by assessors"
    )


class AbstentionResponse(BaseModel):
    """Response from abstention/evidence sufficiency check."""
    status: Literal[
        "READY_FOR_ASSESSOR",
        "NEEDS_MORE_EVIDENCE",
        "ABSTAIN",
        "CONFLICT_REVIEW"
    ]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason_codes: List[str]
    reasons: List[str]
    recommended_action: str
    next_task_id: Optional[str] = None
    metadata: dict


class ShouldAbstainRequest(BaseModel):
    """Request for simple abstention check."""
    competencies: List[dict] = Field(
        ..., min_length=1,
        description="List of competency dictionaries"
    )
    threshold_evidence_coverage: float = Field(
        0.4, ge=0.0, le=1.0,
        description="Minimum acceptable evidence coverage"
    )
    threshold_evidence_confidence: float = Field(
        0.4, ge=0.0, le=1.0,
        description="Minimum acceptable evidence confidence"
    )


class ShouldAbstainResponse(BaseModel):
    """Response for simple abstention check."""
    should_abstain: bool
    reason: str
    reasons: List[str]


class AbstentionReasonsResponse(BaseModel):
    """Response containing reasons for abstention consideration."""
    worker_id: str = Field(..., min_length=1)
    reasons: List[str]
    total_competencies: int
    mandatory_competencies: int