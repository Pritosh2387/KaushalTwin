"""
KaushalTwin ML Service — Pydantic Schemas: Certification Recommendation (Module 9)
"""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class CertificationBasisSchema(BaseModel):
    """Schema for the basis of certification recommendation."""
    competency_score: float = Field(..., ge=0, le=100)
    evidence_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    mandatory_nos_complete: bool
    critical_conflicts: int = Field(..., ge=0)
    overall_readiness_score: float = Field(..., ge=0.0, le=100.0)


class CertificationRecommendationRequest(BaseModel):
    """Request for certification recommendation."""
    worker_id: str = Field(..., min_length=1)
    competency_profile: List[dict] = Field(
        ..., min_length=1,
        description="List of competency dictionaries from competency twin"
    )
    skill_gap_analysis: Optional[dict] = Field(
        None,
        description="Results from skill gap analysis"
    )
    abstention_decision: Optional[dict] = Field(
        None,
        description="Results from abstention/evidence sufficiency check"
    )
    calibration_info: Optional[dict] = Field(
        None,
        description="Results from assessor calibration"
    )


class CertificationRecommendationResponse(BaseModel):
    """Response from certification recommendation."""
    recommendation: Literal[
        "RECOMMEND_CERTIFICATION",
        "CONDITIONAL_RECOMMENDATION",
        "MORE_EVIDENCE_REQUIRED",
        "NOT_YET_READY",
        "ABSTAIN",
        "CONFLICT_REVIEW"
    ]
    confidence: float = Field(..., ge=0.0, le=1.0)
    basis: CertificationBasisSchema
    assessor_action: str
    ai_authority: Literal["RECOMMENDATION_ONLY"]


class CompetencyProfileSummaryResponse(BaseModel):
    """Response for competency profile summary."""
    worker_id: str = Field(..., min_length=1)
    total_nos: int
    mandatory_count: int
    average_competency_score: float
    average_evidence_confidence: float
    average_evidence_coverage: float
    competency_distribution: dict