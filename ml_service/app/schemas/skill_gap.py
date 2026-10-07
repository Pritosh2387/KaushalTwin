"""
KaushalTwin ML Service — Pydantic Schemas: Skill Gap + Evidence Debt (Module 6)
"""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


class NOSGapInput(BaseModel):
    """Input for a single NOS competency (from competency twin)."""
    nos_id: str = Field(..., min_length=1)
    competency_score: int = Field(..., ge=0, le=100)
    evidence_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    mandatory: bool = False
    supporting_evidence: Optional[List[str]] = None
    missing_evidence: Optional[List[str]] = None

    @field_validator("evidence_confidence")
    @classmethod
    def validate_evidence_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("evidence_confidence must be between 0.0 and 1.0")
        return v


class SkillGapRequest(BaseModel):
    """Request for skill gap analysis."""
    worker_id: str = Field(..., min_length=1)
    competencies: List[NOSGapInput] = Field(..., min_length=1)
    evidence_records: Optional[List[dict]] = Field(
        None,
        description="Optional evidence records for detailed analysis"
    )


class NOSGapOutput(BaseModel):
    """Output for a single NOS gap analysis."""
    nos_id: str
    mandatory: bool
    competency_score: int = Field(..., ge=0, le=100)
    evidence_confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    evidence_debt: float = Field(..., ge=0.0, le=1.0)
    missing_evidence: List[str]
    supporting_evidence: List[str]
    status: Literal["STRONG", "WEAK", "MISSING"]
    reason: str


class SkillGapResponse(BaseModel):
    """Response from skill gap analysis."""
    worker_id: str
    overall_evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    overall_evidence_debt: float = Field(..., ge=0.0, le=1.0)
    gaps: List[NOSGapOutput]
    summary: dict


class EvidenceDebtRequest(BaseModel):
    """Request for evidence debt calculation."""
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)


class EvidenceDebtResponse(BaseModel):
    """Response for evidence debt calculation."""
    evidence_coverage: float
    evidence_debt: float
    interpretation: str


class MissingEvidenceRequest(BaseModel):
    """Request for missing evidence identification."""
    nos_id: str = Field(..., min_length=1)
    mandatory: bool = False
    current_evidence: List[str] = Field(default_factory=list)
    required_evidence_types: List[str] = Field(
        default_factory=lambda: [
            "SELF_DECLARATION",
            "PRACTICAL_OBSERVATION",
            "ASSESSOR_VALIDATION",
            "DOCUMENTATION"
        ]
    )


class MissingEvidenceResponse(BaseModel):
    """Response for missing evidence identification."""
    nos_id: str
    mandatory: bool
    current_evidence: List[str]
    missing_evidence: List[str]
    required_evidence_types: List[str]
    evidence_debt: float