"""
KaushalTwin ML Service — Pydantic Schemas: Explainability + Audit Trail + Decision Report (Module 10)
"""
from __future__ import annotations

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class EvidenceWithProvenanceSchema(BaseModel):
    """Schema for evidence with provenance tracking."""
    type: Literal["DECLARED", "OBSERVED", "ASSESSED", "INFERRED", "DERIVED"]
    description: str
    strength: float = Field(..., ge=0.0, le=1.0)
    importance: float = Field(..., ge=0.0)


class ExplainableClaimResponse(BaseModel):
    """Response from claim explanation."""
    claim: str
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "WEAKLY_SUPPORTED", "INSUFFICIENT_EVIDENCE"]
    supporting_evidence: List[EvidenceWithProvenanceSchema]
    missing_evidence: List[EvidenceWithProvenanceSchema]
    explanation_summary: str


class AuditEventRequest(BaseModel):
    """Request for generating an audit event."""
    worker_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    module: str = Field(..., min_length=1)
    input_summary: dict = Field(..., description="Summary of inputs to the action")
    output_summary: dict = Field(..., description="Summary of outputs from the action")
    assessor_id: Optional[str] = Field(None, description="Assessor ID if applicable")
    previous_state: Optional[dict] = Field(None, description="State before action")
    new_state: Optional[dict] = Field(None, description="State after action")
    evidence_references: Optional[List[str]] = Field(None, description="References to evidence used")
    model_info: Optional[dict] = Field(None, description="Information about models/methods used")


class AuditEventResponse(BaseModel):
    """Response from audit event generation."""
    timestamp: str
    worker_id: str
    assessor_id: Optional[str] = None
    action: str
    module: str
    input_summary: dict
    output_summary: dict
    previous_state: Optional[dict] = None
    new_state: Optional[dict] = None
    evidence_references: List[str]
    model_info: dict
    hash: str
    hash_algorithm: str = "SHA-256"


class AuditVerificationRequest(BaseModel):
    """Request for verifying an audit event."""
    audit_event: dict = Field(..., description="Audit event to verify")


class AuditVerificationResponse(BaseModel):
    """Response from audit event verification."""
    is_valid: bool
    reason: Optional[str] = None


class DecisionReportRequest(BaseModel):
    """Request for generating a decision report."""
    worker_id: str = Field(..., min_length=1)
    worker_info: dict = Field(..., description="Basic worker information")
    skills_extracted: List[dict] = Field(
        ..., description="Results from skill extraction"
    )
    nos_mapping: List[dict] = Field(
        ..., description="Results from NOS mapping"
    )
    competency_profile: List[dict] = Field(
        ..., description="Results from competency scoring"
    )
    evidence_summary: dict = Field(..., description="Summary of evidence analysis")
    skill_gaps: List[dict] = Field(..., description="Results from skill gap analysis")
    assessment_summary: dict = Field(..., description="Summary of assessment tasks completed")
    abstention_result: dict = Field(..., description="Results from evidence sufficiency check")
    calibration_info: Optional[dict] = Field(
        None,
        description="Results from assessor calibration (optional)"
    )
    certification_recommendation: Optional[dict] = Field(
        None,
        description="Results from certification recommendation (optional)"
    )
    explanation: Optional[dict] = Field(
        None,
        description="Explainability analysis (optional)"
    )
    audit_event: Optional[dict] = Field(
        None,
        description="Audit trail information (optional)"
    )


class DecisionReportResponse(BaseModel):
    """Response from decision report generation."""
    worker: dict
    skills: List[dict]
    nos_mapping: List[dict]
    competency_profile: List[dict]
    evidence_summary: dict
    skill_gaps: List[dict]
    assessment_summary: dict
    abstention: dict
    calibration: Optional[dict] = None
    recommendation: Optional[dict] = None
    explanation: Optional[dict] = None
    audit: Optional[dict] = None
    metadata: dict