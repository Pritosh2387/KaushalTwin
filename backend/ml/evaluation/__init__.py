"""
KaushalTwin ML Service — Evaluation, Calibration & Fairness Package (Module 10)
"""

from ml.evaluation.models import EvaluationExample, EvaluationDataset
from ml.evaluation.metrics import (
    evaluate_skill_extraction,
    evaluate_nos_mapping,
    evaluate_abstention,
    aggregate_abstention_metrics,
)
from ml.evaluation.calibration import (
    ScoreSemantics,
    assert_score_semantic,
    PlattScaler,
    IsotonicCalibrator,
    calculate_ece,
    generate_reliability_diagram,
)
from ml.evaluation.agreement import (
    compute_cohen_kappa,
    compute_weighted_kappa,
    compute_fleiss_kappa,
    compute_krippendorff_alpha,
    evaluate_ai_assessor_alignment,
)
from ml.evaluation.fairness import audit_fairness_slices
from ml.evaluation.framework import PipelineEvaluator

__all__ = [
    "EvaluationExample",
    "EvaluationDataset",
    "evaluate_skill_extraction",
    "evaluate_nos_mapping",
    "evaluate_abstention",
    "aggregate_abstention_metrics",
    "ScoreSemantics",
    "assert_score_semantic",
    "PlattScaler",
    "IsotonicCalibrator",
    "calculate_ece",
    "generate_reliability_diagram",
    "compute_cohen_kappa",
    "compute_weighted_kappa",
    "compute_fleiss_kappa",
    "compute_krippendorff_alpha",
    "evaluate_ai_assessor_alignment",
    "audit_fairness_slices",
    "PipelineEvaluator",
]
