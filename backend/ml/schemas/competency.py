"""
KaushalTwin ML Service — Pydantic Schemas: Competency Twin (Module 3)
"""

from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CriterionInput(BaseModel):
    id: Optional[str] = None
    name: str
    score: Optional[float] = Field(None, ge=0)
    weight: float = Field(..., gt=0)
    max_score: float = Field(5.0, gt=0)


class NOSCompetencyInput(BaseModel):
    nos_id: str
    criteria: list[CriterionInput] = Field(..., min_length=1)
    mandatory: bool = False
    importance: float = Field(1.0, ge=0.0, le=2.0)
    evidence_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    required_criteria_ids: Optional[list[str]] = None

    @field_validator("nos_id")
    @classmethod
    def nos_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("nos_id cannot be blank")
        return v


class CompetencyScoreRequest(BaseModel):
    nos_id: str
    criteria: list[CriterionInput] = Field(..., min_length=1)
    mandatory: bool = False
    importance: float = Field(1.0, ge=0.0, le=2.0)
    evidence_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    required_criteria_ids: Optional[list[str]] = None


class ScoringDetail(BaseModel):
    raw_score: float
    total_weight: float
    observed_count: int
    max_possible: float


class CompetencyScoreResponse(BaseModel):
    nos_id: str
    competency_score: int = Field(..., ge=0, le=100)
    evidence_confidence: Optional[float] = Field(None, description="Null until future confidence engine")
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    mandatory: bool
    importance: float
    status: Literal["UNASSESSED", "IN_PROGRESS", "EVIDENCE_AVAILABLE"]
    scoring_detail: ScoringDetail


class CompetencyTwinRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)
    competencies: list[NOSCompetencyInput] = Field(..., min_length=1)


class CompetencySummary(BaseModel):
    total_nos: int
    mandatory_nos: int
    all_mandatory_assessed: bool
    mandatory_coverage_mean: float


class CompetencyTwinResponse(BaseModel):
    worker_id: str
    competencies: list[CompetencyScoreResponse]
    summary: CompetencySummary
