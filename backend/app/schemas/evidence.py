"""
KaushalTwin Backend — Pydantic Schemas: Evidence
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


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
        ..., description="VERIFIED | REJECTED | PENDING_REVIEW"
    )
    verification_notes: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    assessment_id: Optional[uuid.UUID]
    uploaded_by_id: uuid.UUID
    evidence_type: str
    source_type: str
    description: str
    nos_id: Optional[str]
    file_name: Optional[str]
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    content_hash: Optional[str]
    verification_status: str
    verification_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
    skip: int
    limit: int
