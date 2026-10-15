"""
KaushalTwin Backend — MongoDB Domain Models

Pydantic-backed domain models with serialization helpers for MongoDB.
All entities use UUID identifiers (stored as strings in MongoDB documents).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.db.enums import (
    UserRole,
    AssessmentLifecycle,
    TaskStatus,
    TaskSelectionSource,
    DecisionAction,
    RunStatus,
    EvidenceType,
    EvidenceSourceType,
    EvidenceVerificationStatus,
    AuditEventType,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoBaseModel(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}

    def to_mongo(self) -> dict[str, Any]:
        """Convert model to a MongoDB-storable document with string UUIDs and ISO datetimes."""
        data = self.model_dump()
        for k, v in list(data.items()):
            if isinstance(v, uuid.UUID):
                data[k] = str(v)
            elif isinstance(v, list):
                data[k] = [str(x) if isinstance(x, uuid.UUID) else x for x in v]
        return data

    @classmethod
    def from_mongo(cls, doc: Optional[dict[str, Any]]):
        """Construct model from a MongoDB document."""
        if doc is None:
            return None
        doc_copy = dict(doc)
        doc_copy.pop("_id", None)
        for k, v in list(doc_copy.items()):
            if isinstance(v, datetime) and v.tzinfo is None:
                doc_copy[k] = v.replace(tzinfo=timezone.utc)
        if "work_narrative" not in doc_copy or doc_copy.get("work_narrative") is None:
            doc_copy["work_narrative"] = doc_copy.get("informal_work_description")
        if "informal_work_description" not in doc_copy or doc_copy.get("informal_work_description") is None:
            doc_copy["informal_work_description"] = doc_copy.get("work_narrative")
        return cls.model_validate(doc_copy)


class User(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.WORKER
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class WorkerProfile(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: Optional[uuid.UUID] = None
    registered_by_id: Optional[uuid.UUID] = None
    full_name: str
    trade: str
    years_of_experience: int = 0
    experience_summary: Optional[str] = None
    education_summary: Optional[str] = None
    assessment_status: str = "NOT_STARTED"
    phone: Optional[str] = None
    email: Optional[str] = None
    education_level: Optional[str] = None
    declared_skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    previous_employment: Optional[str] = None
    informal_work_description: Optional[str] = None
    work_narrative: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class EvidenceRecord(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    worker_id: uuid.UUID
    assessment_id: Optional[uuid.UUID] = None
    uploaded_by_id: Optional[uuid.UUID] = None
    evidence_type: str = "OTHER"
    source_type: str = "SELF"
    description: str
    nos_id: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    verification_status: str = "UNVERIFIED"
    verification_notes: Optional[str] = None
    verified_by_id: Optional[uuid.UUID] = None
    metadata_json: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Assessment(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    worker_id: uuid.UUID
    assessor_id: uuid.UUID
    trade: str
    status: str = "ENROLLED"
    notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AssessmentTask(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    assessment_id: uuid.UUID
    title: str
    description: Optional[str] = None
    target_nos_id: Optional[str] = None
    ml_task_id: Optional[str] = None
    selection_source: str = "ASSESSOR_ASSIGNED"
    ai_priority_score: Optional[float] = None
    ai_reasons: Optional[str] = None
    status: str = "PENDING"
    score: Optional[float] = None
    assessor_comments: Optional[str] = None
    evidence_references: Optional[str] = None
    evaluation_criteria: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class AIAssessmentRun(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    assessment_id: uuid.UUID
    worker_id: uuid.UUID
    run_status: str = "PENDING"
    recommendation: Optional[str] = None
    ml_response: Optional[Any] = None
    error_detail: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class AssessorDecision(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    assessment_id: uuid.UUID
    assessor_id: uuid.UUID
    action: str
    comments: Optional[str] = None
    modified_recommendation: Optional[str] = None
    ai_run_id: Optional[uuid.UUID] = None
    created_at: datetime = Field(default_factory=utc_now)


class AuditEvent(MongoBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    actor_user_id: Optional[uuid.UUID] = None
    actor_label: str = "system"
    entity_type: str
    entity_id: str
    action: str
    metadata_json: Optional[str] = None
    integrity_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
