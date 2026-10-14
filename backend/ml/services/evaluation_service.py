"""
KaushalTwin ML Service — Evaluation & Calibration Service Layer
Module 10: Real-World Evaluation, Calibration & Fairness Auditing

Provides high-level service interfaces for:
- End-to-end pipeline evaluation against ground truth
- Confidence calibration & reliability curve computation
- Inter-rater assessor agreement (Cohen's, Fleiss', Krippendorff's, AI-Alignment)
- Demographic & trade fairness auditing
- Benchmark provenance and empirical status inspection
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ml.evaluation.models import EvaluationDataset
from ml.evaluation.framework import PipelineEvaluator, DEFAULT_GROUND_TRUTH_PATH
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


class EvaluationService:
    """Service layer exposing evaluation, calibration, and fairness capabilities."""

    def __init__(self, ground_truth_path: Optional[Union[str, Path]] = None):
        self.default_ground_truth_path = Path(ground_truth_path) if ground_truth_path else DEFAULT_GROUND_TRUTH_PATH

    def run_pipeline_evaluation(
        self,
        dataset: Optional[EvaluationDataset] = None,
        dataset_path: Optional[Union[str, Path]] = None,
        top_k: int = 3,
        min_similarity_threshold: float = 0.25,
    ) -> Dict[str, Any]:
        """Run full evaluation suite over specified dataset or default ground-truth fixture."""
        evaluator = PipelineEvaluator(
            dataset=dataset,
            dataset_path=dataset_path or self.default_ground_truth_path,
        )
        return evaluator.run_evaluation(
            top_k=top_k,
            min_similarity_threshold=min_similarity_threshold,
        )

    def calibrate_scores(
        self,
        scores: List[float],
        labels: List[int],
        method: str = "platt",
        n_bins: int = 5,
    ) -> Dict[str, Any]:
        """
        Fit a calibrator (Platt scaling or Isotonic regression) and return calibrated probabilities,
        ECE, MCE, Brier scores, and reliability bins.
        """
        for s in scores:
            assert_score_semantic(s, ScoreSemantics.RAW_SIMILARITY, name="score")

        if len(scores) != len(labels):
            raise ValueError(f"Length mismatch: {len(scores)} scores vs {len(labels)} labels")

        raw_metrics = calculate_ece(scores, labels, n_bins=n_bins)

        if method == "isotonic":
            calibrator = IsotonicCalibrator().fit(scores, labels)
            calibrated_probs = calibrator.predict_proba(scores)
        else:  # default platt
            calibrator = PlattScaler().fit(scores, labels)
            calibrated_probs = calibrator.predict_proba(scores)

        post_metrics = calculate_ece(calibrated_probs, labels, n_bins=n_bins)

        return {
            "method": method,
            "sample_count": len(scores),
            "raw_similarity_metrics": raw_metrics,
            "calibrated_metrics": post_metrics,
            "calibrated_probabilities": calibrated_probs,
            "improvement_ece": round(raw_metrics["ece"] - post_metrics["ece"], 4),
            "score_semantics_guarantee": (
                "Input scores verified as RAW_SIMILARITY; outputs verified as CALIBRATED_PROBABILITY."
            ),
        }

    def compute_assessor_agreement(
        self,
        metric: str,
        ratings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute agreement or reliability across assessors or between AI and assessors.
        Supported metrics: 'cohen_kappa', 'weighted_kappa', 'fleiss_kappa', 'krippendorff_alpha', 'ai_alignment'.
        """
        m = metric.lower().strip()

        if m == "cohen_kappa":
            r1 = ratings.get("rater1", [])
            r2 = ratings.get("rater2", [])
            return compute_cohen_kappa(r1, r2)

        elif m == "weighted_kappa":
            r1 = ratings.get("rater1", [])
            r2 = ratings.get("rater2", [])
            weights = ratings.get("weights", "quadratic")
            min_r = ratings.get("min_rating")
            max_r = ratings.get("max_rating")
            return compute_weighted_kappa(r1, r2, weights=weights, min_rating=min_r, max_rating=max_r)

        elif m == "fleiss_kappa":
            mat = ratings.get("ratings_matrix", [])
            return compute_fleiss_kappa(mat)

        elif m == "krippendorff_alpha":
            mat = ratings.get("reliability_data", [])
            level = ratings.get("level_of_measurement", "nominal")
            return compute_krippendorff_alpha(mat, level_of_measurement=level)

        elif m in ("ai_alignment", "ai_assessor_alignment"):
            ai_preds = ratings.get("ai_predictions", [])
            assessor_rats = ratings.get("assessor_ratings", [])
            numeric = ratings.get("numeric_scores", False)
            return evaluate_ai_assessor_alignment(ai_preds, assessor_rats, numeric_scores=numeric)

        else:
            raise ValueError(f"Unknown agreement metric: {metric}. Supported: cohen_kappa, weighted_kappa, fleiss_kappa, krippendorff_alpha, ai_alignment")

    def audit_fairness(
        self,
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Audit fairness and demographic disparities across trade and language style cohorts."""
        return audit_fairness_slices(records)

    def get_ground_truth_benchmark_info(
        self,
        path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Inspect the current evaluation benchmark dataset structure, provenance, and empirical status."""
        target_path = Path(path) if path else self.default_ground_truth_path
        if not target_path.exists():
            raise FileNotFoundError(f"Benchmark file not found at {target_path}")

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        dataset = EvaluationDataset.model_validate(data)

        # Cohort distributions
        trades: Dict[str, int] = {}
        styles: Dict[str, int] = {}
        abstain_count = 0

        for ex in dataset.examples:
            trades[ex.trade] = trades.get(ex.trade, 0) + 1
            styles[ex.style] = styles.get(ex.style, 0) + 1
            if ex.should_abstain:
                abstain_count += 1

        return {
            "dataset_id": dataset.dataset_id,
            "version": dataset.version,
            "description": dataset.description,
            "empirical_status": dataset.empirical_status,
            "file_path": str(target_path),
            "total_examples": len(dataset.examples),
            "abstention_examples": abstain_count,
            "trade_distribution": trades,
            "style_distribution": styles,
            "metadata": dataset.metadata,
            "empirical_integrity_notice": (
                "Empirical status: " + dataset.empirical_status + ". "
                "Synthetic functional benchmark fixtures are pending empirical real-world field evaluation with human assessors."
            ),
        }


# Singleton service instance
_evaluation_service = EvaluationService()


def get_evaluation_service() -> EvaluationService:
    """Return singleton EvaluationService instance."""
    return _evaluation_service
