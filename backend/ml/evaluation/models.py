"""
KaushalTwin ML Service — Evaluation Framework: Data Models
Module 10: Real-World Evaluation, Calibration & Fairness Auditing
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class EvaluationExample(BaseModel):
    """
    Ground-truth or synthetic evaluation example for skill extraction and NOS mapping.

    Represents a single evaluated worker statement with expert annotations,
    acceptable alternatives, abstention requirements, and provenance metadata.
    """
    example_id: str = Field(..., description="Unique example identifier")
    worker_statement: str = Field(..., description="Worker transcript or spoken statement")
    trade: str = Field(..., description="Trade domain (electrician, plumber, welder, mason, general)")
    language: str = Field(default="en", description="Language code (en, hi, hinglish, etc.)")
    style: str = Field(default="standard", description="Writing/speaking style (formal, colloquial, code_switched, terse, descriptive)")

    expert_skills: List[str] = Field(default_factory=list, description="Expert-identified skills present in transcript")
    expert_nos_ids: List[str] = Field(default_factory=list, description="Primary expert-approved NOS/QP codes")
    acceptable_alternatives: List[str] = Field(default_factory=list, description="Acceptable alternative or equivalent NOS codes across official/demo catalogs")

    should_abstain: bool = Field(default=False, description="Whether the model should abstain due to out-of-domain or insufficient content")
    evidence_sufficiency: Optional[str] = Field(default="SUFFICIENT", description="Evidence sufficiency status (SUFFICIENT, INSUFFICIENT, AMBIGUOUS)")

    reviewer_id: str = Field(default="REV-SYSTEM-01", description="Pseudonymous reviewer or annotator ID")
    review_status: str = Field(
        default="SYNTHETIC_FIXTURE_PENDING_EMPIRICAL",
        description="Status: EXPERT_VERIFIED, SYNTHETIC_FIXTURE_PENDING_EMPIRICAL, or DISPUTED"
    )

    dataset_provenance: Dict[str, Any] = Field(
        default_factory=lambda: {
            "source_type": "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL",
            "source_name": "KaushalTwin Internal Benchmark Suite",
            "version": "1.0.0",
            "empirical_status": "PENDING_REAL_WORLD_EVALUATION"
        },
        description="Dataset source and integrity metadata"
    )

    annotation_disagreements: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Documented disagreements between multiple annotators"
    )

    qualification_validity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Validity context of the referenced standards (NQR code, status, active dates)"
    )

    @model_validator(mode="after")
    def validate_content(self) -> EvaluationExample:
        if not self.worker_statement.strip():
            raise ValueError("Worker statement cannot be empty")
        if not self.should_abstain and not self.expert_nos_ids and not self.expert_skills:
            raise ValueError("Non-abstention examples must specify expert_skills or expert_nos_ids")
        return self


class EvaluationDataset(BaseModel):
    """Container for ground-truth benchmark datasets."""
    dataset_id: str = Field(..., description="Identifier for dataset")
    version: str = Field(default="1.0.0", description="Dataset version")
    description: str = Field(..., description="Dataset description and purpose")
    empirical_status: str = Field(
        default="SYNTHETIC_FIXTURE_PENDING_EMPIRICAL",
        description="Whether this represents verified empirical field data or synthetic functional fixtures"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    examples: List[EvaluationExample] = Field(default_factory=list, description="List of evaluation examples")
