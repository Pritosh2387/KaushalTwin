"""
KaushalTwin ML Service — Pydantic Schemas: Evidence (Module 4)
"""

from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    source: str = Field(..., description="Evidence provenance: PRACTICAL, ASSESSED, OBSERVED, SELF_DECLARATION, DECLARED, INFERRED, EMPLOYER, PEER")
    supports: bool = Field(..., description="Whether this evidence supports the competency")
    notes: Optional[str] = None


class EvidenceAnalysisRequest(BaseModel):
    evidence: list[EvidenceRecord] = Field(..., min_length=1)
    custom_weights: Optional[dict[str, float]] = Field(
        None,
        description="Override default source reliability weights. Keys are source names (uppercase)."
    )


class SourceFeature(BaseModel):
    source: str
    reliability_weight: float
    supports: bool
    observed: bool


class EvidenceAnalysisResponse(BaseModel):
    source_features: list[SourceFeature]
    support_score: float
    contradict_score: float
    independent_sources: int
    conflict: bool
    conflict_reason: Optional[str]


class EvidenceConflictRequest(BaseModel):
    evidence: list[EvidenceRecord] = Field(..., min_length=1)
    custom_weights: Optional[dict[str, float]] = None


class EvidenceConflictResponse(BaseModel):
    conflict: bool
    reason: Optional[str]
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH"]]
    support_score: float
    contradict_score: float


class EvidenceHashRequest(BaseModel):
    content_base64: str = Field(..., description="Base64-encoded file/content bytes to hash")


class EvidenceHashResponse(BaseModel):
    sha256: str
    size_bytes: int
    integrity_status: Literal["VERIFIED"] = "VERIFIED"


class DuplicateCheckRequest(BaseModel):
    hashes: list[str] = Field(..., min_length=1, description="List of SHA-256 hex digests to check")


class DuplicateCheckResponse(BaseModel):
    duplicate_groups: list[list[str]]
    has_duplicates: bool
    total_hashes: int
    duplicate_count: int
