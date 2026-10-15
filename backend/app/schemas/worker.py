"""
KaushalTwin Backend — Pydantic Schemas: Worker
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WorkerCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    trade: str = Field(..., min_length=1, max_length=255)
    years_of_experience: int = Field(0, ge=0, le=70)
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    user_id: Optional[uuid.UUID] = None  # Link to existing user account


class WorkerUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    trade: Optional[str] = Field(None, min_length=1, max_length=255)
    years_of_experience: Optional[int] = Field(None, ge=0, le=70)
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education_level: Optional[str] = None
    declared_skills: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    previous_employment: Optional[str] = None
    informal_work_description: Optional[str] = None
    work_narrative: Optional[str] = Field(None, max_length=10000)


class WorkerResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    trade: str
    years_of_experience: int
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    assessment_status: str
    user_id: Optional[uuid.UUID] = None
    registered_by_id: Optional[uuid.UUID] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    education_level: Optional[str] = None
    declared_skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    previous_employment: Optional[str] = None
    informal_work_description: Optional[str] = None
    work_narrative: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkerNarrativeRequest(BaseModel):
    narrative: str = Field(..., min_length=5, max_length=10000, description="Worker's spoken or typed work narrative")

    @field_validator("narrative")
    @classmethod
    def narrative_not_blank(cls, v: str) -> str:
        if not v or not v.strip() or len(v.strip()) < 5:
            raise ValueError("Narrative must contain at least 5 characters describing your work experience")
        return v.strip()


class WorkerNarrativeAnalyzeRequest(BaseModel):
    narrative: Optional[str] = Field(None, max_length=10000)
    language: str = Field("en", description="Language code (en or hi)")


class WorkerNarrativeAnalyzeResponse(BaseModel):
    worker_id: uuid.UUID
    trade: str
    language: str
    narrative: str
    extracted_skills: list[dict] = Field(default_factory=list)
    nos_mappings: list[dict] = Field(default_factory=list)
    disclaimer: str = (
        "AI suggestions are strictly advisory and awaiting assessor review. "
        "These suggestions do not represent official certification or assessor verification."
    )


class WorkerListResponse(BaseModel):
    items: list[WorkerResponse]
    total: int
    skip: int
    limit: int


class WorkerCompetencyProfileResponse(BaseModel):
    worker_id: uuid.UUID
    trade: str
    assessment_status: str
    latest_ai_run_id: Optional[uuid.UUID] = None
    competencies: list[dict] = []
    summary: Optional[dict] = None
    skills_extracted: list[dict] = []
    nos_candidates: list[dict] = []
    has_profile: bool = False
