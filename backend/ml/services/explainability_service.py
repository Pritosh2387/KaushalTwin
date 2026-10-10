"""
KaushalTwin ML Service — Service: Explainability + Audit Trail + Decision Report (Module 10)
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from ml.algorithms.explainability import (
    explain_claim,
    generate_audit_event,
    verify_audit_event,
    generate_decision_report,
    ProvenanceType,
    EvidenceWithProvenance,
    ExplainableClaim,
)


class ExplainabilityService:
    """Service for explainability, audit trail, and decision reporting."""

    @staticmethod
    def explain_claim(
        claim: str,
        worker_declaration: Optional[str] = None,
        observed_evidence: Optional[List[Dict[str, Any]]] = None,
        assessed_evidence: Optional[List[Dict[str, Any]]] = None,
        inferred_evidence: Optional[List[Dict[str, Any]]] = None,
        derived_evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Explain a claim with provenance tracking.

        Args:
            claim: The claim being evaluated
            worker_declaration: What the worker declared about this claim
            observed_evidence: Evidence from direct observation
            assessed_evidence: Evidence from assessor evaluation
            inferred_evidence: Evidence inferred from other facts
            derived_evidence: Evidence derived through calculations/algorithms

        Returns:
            Dictionary with explainable claim information
        """
        result = explain_claim(
            claim=claim,
            worker_declaration=worker_declaration,
            observed_evidence=observed_evidence,
            assessed_evidence=assessed_evidence,
            inferred_evidence=inferred_evidence,
            derived_evidence=derived_evidence,
        )
        # Convert dataclasses to dicts for JSON serialization
        return {
            "claim": result.claim,
            "status": result.status,
            "supporting_evidence": [
                {
                    "type": e.type.value,
                    "description": e.description,
                    "strength": e.strength,
                    "importance": e.importance,
                }
                for e in result.supporting_evidence
            ],
            "missing_evidence": [
                {
                    "type": e.type.value,
                    "description": e.description,
                    "strength": e.strength,
                    "importance": e.importance,
                }
                for e in result.missing_evidence
            ],
            "explanation_summary": result.explanation_summary,
        }

    @staticmethod
    def generate_audit_event(
        worker_id: str,
        action: str,
        module: str,
        input_summary: Dict[str, Any],
        output_summary: Dict[str, Any],
        assessor_id: Optional[str] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        evidence_references: Optional[List[str]] = None,
        model_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an audit record for tracking decisions and actions.

        Args:
            worker_id: Worker being assessed
            action: Action taken (e.g., "skill_gap_analysis", "certification_recommendation")
            module: Module name (e.g., "skill_gap", "certification")
            input_summary: Summary of inputs to the action
            output_summary: Summary of outputs from the action
            assessor_id: Assessor ID if applicable
            previous_state: State before action (if applicable)
            new_state: State after action (if applicable)
            evidence_references: References to evidence used
            model_info: Information about models/methods used

        Returns:
            Dictionary representing the audit event
        """
        return generate_audit_event(
            worker_id=worker_id,
            action=action,
            module=module,
            input_summary=input_summary,
            output_summary=output_summary,
            assessor_id=assessor_id,
            previous_state=previous_state,
            new_state=new_state,
            evidence_references=evidence_references,
            model_info=model_info,
        )

    @staticmethod
    def verify_audit_event(audit_event: Dict[str, Any]) -> bool:
        """
        Verify the integrity of an audit event by checking its hash.

        Args:
            audit_event: Audit event dictionary to verify

        Returns:
            True if audit event is valid, False otherwise
        """
        return verify_audit_event(audit_event)

    @staticmethod
    def generate_decision_report(
        worker_id: str,
        worker_info: Dict[str, Any],
        skills_extracted: List[Dict[str, Any]],
        nos_mapping: List[Dict[str, Any]],
        competency_profile: List[Dict[str, Any]],
        evidence_summary: Dict[str, Any],
        skill_gaps: List[Dict[str, Any]],
        assessment_summary: Dict[str, Any],
        abstention_result: Dict[str, Any],
        calibration_info: Optional[Dict[str, Any]] = None,
        certification_recommendation: Optional[Dict[str, Any]] = None,
        explanation: Optional[Dict[str, Any]] = None,
        audit_event: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive decision report for assessors.

        Args:
            worker_id: Worker identifier
            worker_info: Basic worker information
            skills_extracted: Results from skill extraction
            nos_mapping: Results from NOS mapping
            competency_profile: Results from competency scoring
            evidence_summary: Summary of evidence analysis
            skill_gaps: Results from skill gap analysis
            assessment_summary: Summary of assessment tasks completed
            abstention_result: Results from evidence sufficiency check
            calibration_info: Results from assessor calibration (optional)
            certification_recommendation: Results from certification recommendation (optional)
            explanation: Explainability analysis (optional)
            audit_event: Audit trail information (optional)

        Returns:
            Comprehensive decision report for assessor review
        """
        return generate_decision_report(
            worker_id=worker_id,
            worker_info=worker_info,
            skills_extracted=skills_extracted,
            nos_mapping=nos_mapping,
            competency_profile=competency_profile,
            evidence_summary=evidence_summary,
            skill_gaps=skill_gaps,
            assessment_summary=assessment_summary,
            abstention_result=abstention_result,
            calibration_info=calibration_info,
            certification_recommendation=certification_recommendation,
            explanation=explanation,
            audit_event=audit_event,
        )