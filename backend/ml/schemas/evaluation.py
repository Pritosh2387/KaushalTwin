"""
KaushalTwin ML Service — Evaluation, Calibration & Fairness Schemas
Module 10: Real-World Evaluation, Calibration & Fairness Auditing
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ml.evaluation.models import EvaluationDataset


class EvaluationRunRequest(BaseModel):
    """Request to execute pipeline evaluation."""
    dataset: Optional[EvaluationDataset] = Field(
        default=None,
        description="Optional custom benchmark dataset. If omitted, uses default active ground-truth benchmark."
    )
    dataset_path: Optional[str] = Field(
        default=None,
        description="Optional path to custom benchmark JSON file."
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Top-k candidates for NOS mapping evaluation")
    min_similarity_threshold: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Minimum similarity threshold for abstention"
    )


class EvaluationRunResponse(BaseModel):
    """Response containing complete evaluation metrics, calibration, and fairness audit."""
    dataset_id: str
    version: str
    empirical_status: str
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)
    total_examples: int
    extraction_metrics: Dict[str, Any]
    mapping_metrics: Dict[str, Any]
    abstention_metrics: Dict[str, Any]
    calibration_metrics: Dict[str, Any]
    fairness_audit: Dict[str, Any]
    per_example_results: List[Dict[str, Any]]
    integrity_notice: str


class CalibrationRequest(BaseModel):
    """Request to calibrate raw model scores into empirical probabilities."""
    scores: List[float] = Field(..., description="Raw similarity or model confidence scores in [0.0, 1.0]")
    labels: List[int] = Field(..., description="Ground-truth binary outcomes (1 for match, 0 for non-match)")
    method: str = Field(default="platt", description="Calibration algorithm ('platt' or 'isotonic')")
    n_bins: int = Field(default=5, ge=2, le=20, description="Number of bins for ECE calculation")


class CalibrationResponse(BaseModel):
    """Response containing pre/post calibration ECE, reliability bins, and calibrated probabilities."""
    method: str
    sample_count: int
    raw_similarity_metrics: Dict[str, Any]
    calibrated_metrics: Dict[str, Any]
    calibrated_probabilities: List[float]
    improvement_ece: float
    score_semantics_guarantee: str


class AgreementRequest(BaseModel):
    """Request to compute assessor agreement or AI-assessor alignment."""
    metric: str = Field(
        ...,
        description="Metric type: 'cohen_kappa', 'weighted_kappa', 'fleiss_kappa', 'krippendorff_alpha', or 'ai_alignment'"
    )
    ratings: Dict[str, Any] = Field(
        ...,
        description="Payload containing ratings data suitable for the requested metric"
    )


class AgreementResponse(BaseModel):
    """Response containing computed agreement metric and qualitative interpretation."""
    metric: str
    result: Dict[str, Any]


class FairnessAuditRequest(BaseModel):
    """Request to audit demographic fairness across trade cohorts and transcript styles."""
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of evaluated prediction records with 'trade', 'style', 'extraction_f1', etc."
    )


class FairnessAuditResponse(BaseModel):
    """Response containing trade parity ratio, disparity metrics, and equity recommendations."""
    verdict: str
    trade_parity_ratio: float
    max_trade_disparity: float
    max_style_disparity: float
    false_abstention_disparity: float
    trade_slices: Dict[str, Any]
    style_slices: Dict[str, Any]
    recommendations: List[str]
    assessor_notice: str


class BenchmarkInfoResponse(BaseModel):
    """Response providing metadata and empirical status for the evaluation benchmark suite."""
    dataset_id: str
    version: str
    description: str
    empirical_status: str
    file_path: str
    total_examples: int
    abstention_examples: int
    trade_distribution: Dict[str, int]
    style_distribution: Dict[str, int]
    metadata: Dict[str, Any]
    empirical_integrity_notice: str
