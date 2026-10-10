"""
KaushalTwin ML Service — Pydantic Schemas: Skills & NOS Mapping (Module 2)
"""

from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

class SkillExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Worker transcript or description")
    language: str = Field("en", description="BCP-47 language code")
    trade: str = Field("electrician", description="Trade/occupation context")
    provider: Literal["demo", "llm"] = Field("demo", description="Skill extraction provider")

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text cannot be blank")
        return v


class ExtractedSkill(BaseModel):
    skill_name: str
    normalized_name: str
    evidence_text: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class SkillExtractionResponse(BaseModel):
    skills: list[ExtractedSkill]
    count: int
    provider: str
    trade: str
    language: str


# ---------------------------------------------------------------------------
# NOS mapping
# ---------------------------------------------------------------------------

class NOSMappingRequest(BaseModel):
    skills: list[ExtractedSkill] = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)
    embedding_provider: Literal["demo", "sentence_transformer"] = "demo"


class NOSCandidate(BaseModel):
    nos_id: str
    title: str
    mandatory: bool
    weight: float
    similarity: float = Field(..., ge=0.0, le=1.0)
    signals: dict
    methods: list[str]
    source_type: str
    mapping_status: Literal["SUGGESTED"] = "SUGGESTED"


class SkillNOSMapping(BaseModel):
    skill: ExtractedSkill
    candidates: list[NOSCandidate]


class NOSMappingResponse(BaseModel):
    mappings: list[SkillNOSMapping]
    note: str = "These are CANDIDATE mappings only. Human assessor confirmation is required."


# ---------------------------------------------------------------------------
# NOS search
# ---------------------------------------------------------------------------

class NOSSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    embedding_provider: Literal["demo", "sentence_transformer"] = "demo"


class NOSSearchResult(BaseModel):
    nos_id: str
    title: str
    description: str
    mandatory: bool
    similarity: float
    methods: list[str]
    source_type: str


class NOSSearchResponse(BaseModel):
    results: list[NOSSearchResult]
    query: str
    count: int
