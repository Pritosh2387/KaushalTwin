"""
KaushalTwin ML Service — Pydantic Schemas: Assessor Calibration + Consistency (Module 8)
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AssessorScoreInput(BaseModel):
    """Input for a single assessor score."""
    assessor_id: str = Field(..., min_length=1)
    worker_id: str = Field(..., min_length=1)
    competency_area: str = Field(..., min_length=1)
    score: float = Field(..., description="Score given by assessor")


class AssessorScoresRequest(BaseModel):
    """Request for assessor calibration analysis."""
    assessor_scores: List[AssessorScoreInput] = Field(
        ..., min_length=1,
        description="List of assessor scores for calibration analysis"
    )
    competency_areas: Optional[List[str]] = Field(
        None,
        description="Specific competency areas to analyze (if None, analyzes all)"
    )


class AssessorProfileOutput(BaseModel):
    """Output for an assessor's calibration profile."""
    assessor_id: str
    mean_score: float = Field(..., description="Average score given by this assessor")
    group_mean: float = Field(..., description="Average score across all assessors")
    severity_delta: float = Field(..., description="Difference from group mean (positive=lenient)")
    interpretation: str = Field(..., description="Interpretation of severity delta")
    score_variance: float = Field(..., description="Variance in this assessor's scores")
    total_assessments: int = Field(..., ge=0, description="Number of assessments made")


class CalibrationResultResponse(BaseModel):
    """Response from assessor calibration analysis."""
    assessor_profiles: List[AssessorProfileOutput]
    agreement_metrics: Dict[str, Any]
    disagreement_areas: List[str]
    overall_consistency: str
    recommended_actions: List[str]


class SingleAssessorProfileRequest(BaseModel):
    """Request for single assessor profile."""
    assessor_scores: List[AssessorScoreInput] = Field(
        ..., min_length=1
    )
    assessor_id: str = Field(..., min_length=1)


class AssessorAgreementRequest(BaseModel):
    """Request for agreement between two assessors."""
    assessor_a_scores: List[AssessorScoreInput] = Field(
        ..., min_length=1
    )
    assessor_b_scores: List[AssessorScoreInput] = Field(
        ..., min_length=1
    )