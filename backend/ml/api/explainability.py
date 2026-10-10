"""
KaushalTwin ML Service — API: Explainability + Audit Trail + Decision Report (Module 10)
"""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ml.services.explainability_service import ExplainabilityService
from ml.schemas.explainability import (
    ExplainableClaimResponse,
    AuditEventRequest,
    AuditEventResponse,
    AuditVerificationRequest,
    AuditVerificationResponse,
    DecisionReportRequest,
    DecisionReportResponse,
)

router = APIRouter(prefix="/explainability", tags=["Explainability & Audit Trail"])


@router.post(
    "/explain-claim",
    response_model=ExplainableClaimResponse,
    summary="Explain a claim with provenance tracking",
)
def explain_claim_endpoint(
    claim: str,
    worker_declaration: Optional[str] = None,
    observed_evidence: Optional[List[dict]] = None,
    assessed_evidence: Optional[List[dict]] = None,
    inferred_evidence: Optional[List[dict]] = None,
    derived_evidence: Optional[List[dict]] = None,
) -> ExplainableClaimResponse:
    """
    Explain a claim with provenance tracking (DECLARED, OBSERVED, ASSESSED, INFERRED, DERIVED).

    This implements Part A of Module 10: Explainability.
    """
    try:
        result = ExplainabilityService.explain_claim(
            claim=claim,
            worker_declaration=worker_declaration,
            observed_evidence=observed_evidence,
            assessed_evidence=assessed_evidence,
            inferred_evidence=inferred_evidence,
            derived_evidence=derived_evidence,
        )
        return ExplainableClaimResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EXPLAINABILITY_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/audit-event",
    response_model=AuditEventResponse,
    summary="Generate an audit event for tracking decisions",
)
def create_audit_event(request: AuditEventRequest) -> AuditEventResponse:
    """
    Generate an audit record for tracking decisions and actions.

    This implements Part B of Module 10: Audit Trail.
    """
    try:
        result = ExplainabilityService.generate_audit_event(
            worker_id=request.worker_id,
            action=request.action,
            module=request.module,
            input_summary=request.input_summary,
            output_summary=request.output_summary,
            assessor_id=request.assessor_id,
            previous_state=request.previous_state,
            new_state=request.new_state,
            evidence_references=request.evidence_references,
            model_info=request.model_info,
        )
        return AuditEventResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "AUDIT_EVENT_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/verify-audit",
    response_model=AuditVerificationResponse,
    summary="Verify the integrity of an audit event",
)
def verify_audit_event_endpoint(request: AuditVerificationRequest) -> AuditVerificationResponse:
    """
    Verify the integrity of an audit event by checking its hash.

    This implements Part B of Module 10: Audit Trail.
    """
    try:
        is_valid = ExplainabilityService.verify_audit_event(request.audit_event)
        return AuditVerificationResponse(
            is_valid=is_valid,
            reason=None if is_valid else "Audit event hash verification failed"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "AUDIT_VERIFICATION_ERROR", "message": str(exc)}}
        ) from exc


@router.post(
    "/decision-report",
    response_model=DecisionReportResponse,
    summary="Generate a comprehensive decision report for assessors",
)
def generate_decision_report_endpoint(request: DecisionReportRequest) -> DecisionReportResponse:
    """
    Generate a comprehensive decision report combining all module outputs.

    This implements Part C of Module 10: Decision Report.
    """
    try:
        result = ExplainabilityService.generate_decision_report(
            worker_id=request.worker_id,
            worker_info=request.worker_info,
            skills_extracted=request.skills_extracted,
            nos_mapping=request.nos_mapping,
            competency_profile=request.competency_profile,
            evidence_summary=request.evidence_summary,
            skill_gaps=request.skill_gaps,
            assessment_summary=request.assessment_summary,
            abstention_result=request.abstention_result,
            calibration_info=request.calibration_info,
            certification_recommendation=request.certification_recommendation,
            explanation=request.explanation,
            audit_event=request.audit_event,
        )
        return DecisionReportResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "DECISION_REPORT_ERROR", "message": str(exc)}}
        ) from exc