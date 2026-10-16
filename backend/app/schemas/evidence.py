"""
KaushalTwin Backend — Pydantic Schemas: Evidence
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator


class EvidenceCreateRequest(BaseModel):
    worker_id: uuid.UUID
    assessment_id: Optional[uuid.UUID] = None
    evidence_type: str = Field(..., description="EvidenceType enum value")
    source_type: str = Field(..., description="EvidenceSourceType enum value")
    description: str = Field(..., min_length=1)
    nos_id: Optional[str] = None
    metadata_json: Optional[Any] = None  # JSON-serializable extra metadata


class EvidenceUpdateRequest(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    nos_id: Optional[str] = None


class EvidenceVerifyRequest(BaseModel):
    verification_status: str = Field(
        ..., description="VERIFIED | REJECTED | PENDING_REVIEW | UNVERIFIED"
    )
    verification_notes: Optional[str] = None

    @field_validator("verification_status")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        s = v.upper().strip()
        if s == "NEEDS_INFO":
            return "PENDING_REVIEW"
        if s == "PENDING":
            return "PENDING_REVIEW"
        valid_statuses = {"VERIFIED", "REJECTED", "PENDING_REVIEW", "UNVERIFIED"}
        if s not in valid_statuses:
            raise ValueError(f"Invalid verification status: {v}. Must be one of {valid_statuses}")
        return s


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    assessment_id: Optional[uuid.UUID] = None
    uploaded_by_id: Optional[uuid.UUID] = None
    evidence_type: str
    source_type: str
    description: str
    nos_id: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    verification_status: str
    verification_notes: Optional[str] = None
    verified_by_id: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    skip: int
    limit: int
