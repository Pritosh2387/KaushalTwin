"""
KaushalTwin ML Service — Pydantic Schemas: Skills & NOS Mapping (Module 2)
"""

from __future__ import annotations
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

class SkillExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Worker transcript or description")
    language: str = Field("en", description="BCP-47 language code")
    trade: str = Field("general", description="Trade/occupation context (e.g. electrician, plumber, welder, general)")
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
    # Priority 5 additions — all optional for backward compatibility
    trade_context: Optional[str] = Field(
        None,
        description="Trade domain this skill was extracted from (e.g. electrician, plumber, welder, general)"
    )
    text_span: Optional[str] = Field(
        None,
        description="Original text span from which the skill was extracted"
    )
    extraction_method: Optional[str] = Field(
        None,
        description="Method used for extraction (e.g. pattern_match, synonym_expand)"
    )


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
    # Priority 5 additions
    min_similarity_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum combined similarity score for a candidate to be included. "
                    "Set > 0 to suppress very weak matches."
    )
    ambiguity_margin: float = Field(
        0.05,
        ge=0.0,
        le=0.5,
        description="If the top two candidates are within this margin, the mapping is flagged as ambiguous."
    )


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
    # Provenance information for traceability
    provenance: Optional[Dict[str, Any]] = None
    # Priority 5 additions — optional for backward compatibility
    match_reasons: Optional[List[str]] = Field(
        None,
        description="Human-readable explanations of why this NOS was matched"
    )
    ambiguity_flag: Optional[bool] = Field(
        None,
        description="True when this candidate is ambiguous with another nearby candidate"
    )
    trade_match: Optional[bool] = Field(
        None,
        description="True when the NOS trade matches the skill's extracted trade context"
    )


class SkillNOSMapping(BaseModel):
    skill: ExtractedSkill
    candidates: list[NOSCandidate]
    # Priority 5 additions
    abstained: bool = Field(
        False,
        description="True when all candidates scored below min_similarity_threshold"
    )
    abstention_reason: Optional[str] = Field(
        None,
        description="Reason for abstention when no confident match was found"
    )


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
    # Provenance information for traceability
    provenance: Optional[Dict[str, Any]] = None


class NOSSearchResponse(BaseModel):
    results: list[NOSSearchResult]
    query: str
    count: int
