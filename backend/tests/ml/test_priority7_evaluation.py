"""
Unit and Integration Tests for Priority 7: Real-World Evaluation, Calibration & Fairness
Module 10: Real-World Evaluation, Confidence Calibration & Fairness Auditing

Validates:
1. Data models and provenance tracking (EvaluationExample, EvaluationDataset).
2. Extraction metrics (Exact & Relaxed Precision/Recall/F1).
3. Mapping metrics (Top-1, Top-k, MRR).
4. Abstention metrics (Confusion matrix, False Abstention Rate, Unsafe Prediction Rate).
5. Score semantics boundaries and invariants.
6. Calibration algorithms (Platt Scaling, Isotonic Regression, ECE, MCE, Brier score).
7. Inter-rater reliability (Cohen's Kappa, Weighted Kappa, Fleiss' Kappa, Krippendorff's Alpha, AI alignment).
8. Fairness & Disparity auditing (Trade Parity Ratio, Four-Fifths Rule, False Abstention Disparity).
9. PipelineEvaluator end-to-end execution on benchmark suite without network calls.
10. EvaluationService and FastAPI REST endpoints under /api/v1/ml/evaluation/.
"""

import math
import pytest
from fastapi.testclient import TestClient

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
from ml.services.evaluation_service import get_evaluation_service
from ml.main import app as ml_app


@pytest.fixture
def api_client():
    """TestClient for ML FastAPI service."""
    return TestClient(ml_app)


# ---------------------------------------------------------------------------
# 1. Models & Validation
# ---------------------------------------------------------------------------

def test_evaluation_example_validation():
    """Verify validation constraints on EvaluationExample."""
    # Valid example
    ex = EvaluationExample(
        example_id="EX-TEST-01",
        worker_statement="I install PVC conduits and pull copper wires.",
        trade="electrician",
        expert_skills=["pvc conduit installation", "wire pulling"],
        expert_nos_ids=["ELE/N9401"],
    )
    assert ex.example_id == "EX-TEST-01"
    assert ex.review_status == "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL"

    # Empty worker statement must be rejected
    with pytest.raises(ValueError, match="Worker statement cannot be empty"):
        EvaluationExample(
            example_id="EX-EMPTY",
            worker_statement="   ",
            trade="electrician",
            expert_skills=["conduit installation"],
        )

    # Non-abstention example with no skills or NOS must be rejected
    with pytest.raises(ValueError, match="Non-abstention examples must specify expert_skills or expert_nos_ids"):
        EvaluationExample(
            example_id="EX-NO-TARGETS",
            worker_statement="I work on electrical systems.",
            trade="electrician",
            should_abstain=False,
            expert_skills=[],
            expert_nos_ids=[],
        )

    # Abstention example without targets is valid
    abst_ex = EvaluationExample(
        example_id="EX-ABST-01",
        worker_statement="Today the weather is very hot.",
        trade="general",
        should_abstain=True,
    )
    assert abst_ex.should_abstain is True


def test_evaluation_dataset_loading():
    """Verify loading benchmark ground truth fixture with empirical provenance."""
    service = get_evaluation_service()
    info = service.get_ground_truth_benchmark_info()
    assert info["total_examples"] == 20
    assert info["empirical_status"] == "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL"
    assert "electrician" in info["trade_distribution"]
    assert "plumber" in info["trade_distribution"]
    assert "welder" in info["trade_distribution"]
    assert "mason" in info["trade_distribution"]
    assert info["abstention_examples"] >= 2


# ---------------------------------------------------------------------------
# 2. Skill Extraction Metrics
# ---------------------------------------------------------------------------

def test_evaluate_skill_extraction_exact_and_relaxed():
    """Test exact and relaxed (token overlap) skill extraction metrics."""
    extracted = ["pvc conduit installation", "wire pulling", "switchboard fixing"]
    ground_truth = ["conduit installation", "wire pulling", "earthing"]

    res = evaluate_skill_extraction(extracted, ground_truth, token_overlap_threshold=0.5)

    # Exact: only 'wire pulling' matches exactly
    assert res["exact_precision"] == round(1 / 3, 4)
    assert res["exact_recall"] == round(1 / 3, 4)
    assert res["exact_f1"] == round(1 / 3, 4)

    # Relaxed: 'pvc conduit installation' overlaps with 'conduit installation', plus 'wire pulling'
    assert res["relaxed_precision"] == round(2 / 3, 4)
    assert res["relaxed_recall"] == round(2 / 3, 4)
    assert res["relaxed_f1"] == round(2 / 3, 4)


def test_evaluate_skill_extraction_empty():
    """Test edge cases with empty extraction or empty ground truth."""
    # Both empty
    res = evaluate_skill_extraction([], [])
    assert res["exact_f1"] == 1.0
    assert res["relaxed_f1"] == 1.0

    # Model extracted nothing but ground truth expected skills
    res = evaluate_skill_extraction([], ["conduit installation"])
    assert res["exact_f1"] == 0.0
    assert res["relaxed_f1"] == 0.0

    # Model hallucinated skills on empty ground truth
    res = evaluate_skill_extraction(["conduit installation"], [])
    assert res["exact_f1"] == 0.0
    assert res["relaxed_f1"] == 0.0


# ---------------------------------------------------------------------------
# 3. NOS Mapping Metrics
# ---------------------------------------------------------------------------

def test_evaluate_nos_mapping():
    """Test Top-1, Top-k, and MRR calculations."""
    candidates = [
        {"nos_id": "ELE/N9402", "title": "Other NOS", "similarity": 0.85},
        {"nos_id": "ELE/N9401", "title": "Install cables", "similarity": 0.75},
        {"nos_id": "ELE/N9403", "title": "Fix fittings", "similarity": 0.60},
    ]

    # Target is ELE/N9401, rank 2
    res = evaluate_nos_mapping(candidates, ground_truth_ids=["ELE/N9401"], top_k=3)
    assert res["top_1_accuracy"] == 0.0
    assert res["top_k_accuracy"] == 1.0
    assert res["reciprocal_rank"] == 0.5
    assert res["match_rank"] == 2
    assert res["matched_id"] == "ELE/N9401"

    # Top-1 match
    res1 = evaluate_nos_mapping(candidates, ground_truth_ids=["ELE/N9402"], top_k=3)
    assert res1["top_1_accuracy"] == 1.0
    assert res1["top_k_accuracy"] == 1.0
    assert res1["reciprocal_rank"] == 1.0

    # Match in acceptable alternatives
    res_alt = evaluate_nos_mapping(
        candidates,
        ground_truth_ids=["ELE/N9999"],
        acceptable_alternatives=["ELE/N9402"],
        top_k=3,
    )
    assert res_alt["top_1_accuracy"] == 1.0
    assert res_alt["match_found"] is True

    # No match
    res_none = evaluate_nos_mapping(candidates, ground_truth_ids=["PLU/N0101"], top_k=3)
    assert res_none["top_1_accuracy"] == 0.0
    assert res_none["top_k_accuracy"] == 0.0
    assert res_none["reciprocal_rank"] == 0.0
    assert res_none["match_found"] is False


# ---------------------------------------------------------------------------
# 4. Abstention Fidelity Metrics
# ---------------------------------------------------------------------------

def test_abstention_evaluation_and_aggregation():
    """Test abstention confusion categorization and metric aggregation."""
    # True Abstain
    e1 = evaluate_abstention(predicted_abstained=True, ground_truth_should_abstain=True)
    assert e1["category"] == "TRUE_ABSTAIN"
    assert e1["is_correct"] is True

    # True Predict
    e2 = evaluate_abstention(predicted_abstained=False, ground_truth_should_abstain=False)
    assert e2["category"] == "TRUE_PREDICT"
    assert e2["is_correct"] is True

    # False Abstain (rejection of valid trade evidence)
    e3 = evaluate_abstention(predicted_abstained=True, ground_truth_should_abstain=False)
    assert e3["category"] == "FALSE_ABSTAIN"
    assert e3["is_correct"] is False

    # False Predict (hallucination / unsafe prediction on out-of-domain)
    e4 = evaluate_abstention(predicted_abstained=False, ground_truth_should_abstain=True)
    assert e4["category"] == "FALSE_PREDICT"
    assert e4["is_correct"] is False

    # Aggregate
    agg = aggregate_abstention_metrics([e1, e2, e3, e4])
    assert agg["accuracy"] == 0.50
    assert agg["false_abstention_rate"] == 0.50  # fa / (tp + fa) = 1 / 2
    assert agg["unsafe_prediction_rate"] == 0.50  # fp / (ta + fp) = 1 / 2


# ---------------------------------------------------------------------------
# 5. Score Semantics Boundaries
# ---------------------------------------------------------------------------

def test_score_semantics_boundary():
    """Ensure raw similarity, heuristic extraction confidence, and calibrated probabilities are bounded."""
    # Valid quantities
    assert_score_semantic(0.75, ScoreSemantics.RAW_SIMILARITY)
    assert_score_semantic(0.85, ScoreSemantics.CALIBRATED_PROBABILITY)
    assert_score_semantic(85.0, ScoreSemantics.COMPETENCY_SCORE)

    # Out of bounds for RAW_SIMILARITY
    with pytest.raises(ValueError, match="must be in \\[0.0, 1.0\\]"):
        assert_score_semantic(1.5, ScoreSemantics.RAW_SIMILARITY)

    with pytest.raises(ValueError, match="must be in \\[0.0, 1.0\\]"):
        assert_score_semantic(-0.2, ScoreSemantics.CALIBRATED_PROBABILITY)

    # NaN must be rejected
    with pytest.raises(ValueError, match="must be a valid numeric quantity"):
        assert_score_semantic(float("nan"), ScoreSemantics.RAW_SIMILARITY)


# ---------------------------------------------------------------------------
# 6. Confidence Calibration (Platt & Isotonic)
# ---------------------------------------------------------------------------

def test_platt_scaling():
    """Test Platt Scaling parameter fitting and monotonic probability mapping."""
    scores = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    labels = [0, 0, 0, 1, 1, 1]

    scaler = PlattScaler().fit(scores, labels, max_iter=200, lr=0.1)
    assert scaler.is_fitted is True

    probs = scaler.predict_proba(scores)
    assert len(probs) == len(scores)
    # Check monotonicity: higher score -> higher probability
    assert probs[0] < probs[-1]
    assert all(0.0 <= p <= 1.0 for p in probs)

    # Test single float prediction
    p_single = scaler.predict_proba(0.85)
    assert isinstance(p_single, float)
    assert 0.0 <= p_single <= 1.0


def test_isotonic_regression():
    """Test Isotonic Regression via PAVA."""
    scores = [0.1, 0.4, 0.35, 0.8, 0.9]
    labels = [0, 0, 1, 1, 1]

    calibrator = IsotonicCalibrator().fit(scores, labels)
    assert calibrator.is_fitted is True

    probs = calibrator.predict_proba(scores)
    assert all(0.0 <= p <= 1.0 for p in probs)
    # Monotonicity check
    assert probs[0] <= probs[-1]


def test_calculate_ece_and_reliability_diagram():
    """Test Expected Calibration Error and reliability diagram bins."""
    probs = [0.1, 0.2, 0.8, 0.9]
    labels = [0, 0, 1, 1]

    res = calculate_ece(probs, labels, n_bins=5)
    assert "ece" in res
    assert "mce" in res
    assert "brier_score" in res
    assert res["ece"] >= 0.0
    assert res["brier_score"] >= 0.0

    bins = generate_reliability_diagram(probs, labels, n_bins=5)
    assert isinstance(bins, list)
    for b in bins:
        assert "mean_confidence" in b
        assert "empirical_accuracy" in b


# ---------------------------------------------------------------------------
# 7. Assessor Agreement & Inter-Rater Reliability
# ---------------------------------------------------------------------------

def test_cohen_kappa():
    """Test Cohen's Kappa for pair-wise nominal categories."""
    # Perfect agreement
    r1 = ["Pass", "Pass", "Fail", "Pass"]
    r2 = ["Pass", "Pass", "Fail", "Pass"]
    res = compute_cohen_kappa(r1, r2)
    assert res["kappa"] == 1.0
    assert res["observed_agreement"] == 1.0
    assert "Almost Perfect" in res["interpretation"]

    # Partial agreement
    r1 = ["Pass", "Pass", "Fail", "Fail", "Pass"]
    r2 = ["Pass", "Fail", "Fail", "Pass", "Pass"]
    res_partial = compute_cohen_kappa(r1, r2)
    assert -1.0 <= res_partial["kappa"] <= 1.0


def test_weighted_kappa():
    """Test Weighted Cohen's Kappa for ordinal ratings."""
    rater1 = [1, 2, 3, 4, 5]
    rater2 = [1, 2, 3, 4, 4]  # close ratings

    res_quad = compute_weighted_kappa(rater1, rater2, weights="quadratic")
    assert res_quad["weighted_kappa"] > 0.80  # high agreement due to quadratic penalty

    res_lin = compute_weighted_kappa(rater1, rater2, weights="linear")
    assert res_lin["weighted_kappa"] > 0.70


def test_fleiss_kappa():
    """Test Fleiss' Kappa for multiple raters on subjects."""
    # 5 subjects, 3 raters, 2 categories [Fail, Pass]
    # Each row sums to 3
    ratings_matrix = [
        [3, 0],  # 3 raters said Fail
        [0, 3],  # 3 raters said Pass
        [0, 3],  # 3 raters said Pass
        [1, 2],  # 1 Fail, 2 Pass
        [3, 0],  # 3 raters said Fail
    ]
    res = compute_fleiss_kappa(ratings_matrix)
    assert "fleiss_kappa" in res
    assert res["subjects"] == 5
    assert res["raters_per_subject"] == 3
    assert res["fleiss_kappa"] > 0.60


def test_krippendorff_alpha():
    """Test Krippendorff's Alpha with complete and missing data."""
    # 3 raters x 4 subjects (nominal)
    data = [
        [1, 2, 1, 3],
        [1, 2, 1, 3],
        [1, 2, None, 3],  # missing rating on subject 2
    ]
    res = compute_krippendorff_alpha(data, level_of_measurement="nominal")
    assert res["alpha"] >= 0.80
    assert "High Reliability" in res["interpretation"]


def test_ai_assessor_alignment():
    """Test AI alignment evaluation for both categorical and numeric scoring."""
    # Categorical
    ai_preds = ["MET", "MET", "NOT_MET", "MET"]
    assessor = ["MET", "MET", "NOT_MET", "NOT_MET"]
    cat_res = evaluate_ai_assessor_alignment(ai_preds, assessor, numeric_scores=False)
    assert cat_res["agreement_rate"] == 0.75
    assert "cohen_kappa" in cat_res

    # Numeric scores
    ai_scores = [0.85, 0.70, 0.60, 0.90]
    ass_scores = [0.80, 0.68, 0.62, 0.88]
    num_res = evaluate_ai_assessor_alignment(ai_scores, ass_scores, numeric_scores=True)
    assert abs(num_res["mean_bias"]) < 0.05
    assert num_res["pearson_correlation"] > 0.90
    assert num_res["verdict"] == "WELL_ALIGNED"


# ---------------------------------------------------------------------------
# 8. Fairness & Disparity Auditing
# ---------------------------------------------------------------------------

def test_audit_fairness_slices():
    """Test Four-Fifths Rule compliance and False Abstention Rate disparity auditing."""
    records = [
        # Electrician (formal)
        {"trade": "electrician", "style": "formal", "extraction_f1": 0.90, "mapping_top1": 1.0, "mapping_mrr": 1.0, "abstention_eval": {"category": "TRUE_PREDICT"}},
        {"trade": "electrician", "style": "colloquial", "extraction_f1": 0.85, "mapping_top1": 1.0, "mapping_mrr": 1.0, "abstention_eval": {"category": "TRUE_PREDICT"}},
        # Plumber (colloquial)
        {"trade": "plumber", "style": "colloquial", "extraction_f1": 0.80, "mapping_top1": 1.0, "mapping_mrr": 1.0, "abstention_eval": {"category": "TRUE_PREDICT"}},
        # Welder (terse)
        {"trade": "welder", "style": "terse", "extraction_f1": 0.80, "mapping_top1": 1.0, "mapping_mrr": 1.0, "abstention_eval": {"category": "TRUE_PREDICT"}},
        # Mason (hinglish)
        {"trade": "mason", "style": "hinglish", "extraction_f1": 0.75, "mapping_top1": 1.0, "mapping_mrr": 1.0, "abstention_eval": {"category": "TRUE_PREDICT"}},
    ]

    res = audit_fairness_slices(records)
    assert res["verdict"] in ["FAIR", "MODERATE_DISPARITY"]
    assert res["trade_parity_ratio"] >= 0.75  # 0.75 / 0.875
    assert "trade_slices" in res
    assert "style_slices" in res
    assert "electrician" in res["trade_slices"]
    assert "mason" in res["trade_slices"]


# ---------------------------------------------------------------------------
# 9. PipelineEvaluator End-to-End Execution
# ---------------------------------------------------------------------------

def test_pipeline_evaluator_run():
    """Execute end-to-end evaluation on the benchmark ground truth dataset."""
    evaluator = PipelineEvaluator()
    results = evaluator.run_evaluation(top_k=3, min_similarity_threshold=0.20)

    assert results["dataset_id"] == "KAUSHALTWIN_BENCHMARK_V1"
    assert results["empirical_status"] == "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL"
    assert results["total_examples"] == 20

    # Verify extraction metrics structure
    assert "exact" in results["extraction_metrics"]
    assert "relaxed" in results["extraction_metrics"]
    assert results["extraction_metrics"]["relaxed"]["f1"] > 0.0

    # Verify mapping metrics structure
    assert "top_1_accuracy" in results["mapping_metrics"]
    assert "top_3_accuracy" in results["mapping_metrics"]
    assert "mrr" in results["mapping_metrics"]

    # Verify abstention metrics
    assert "false_abstention_rate" in results["abstention_metrics"]
    assert "unsafe_prediction_rate" in results["abstention_metrics"]

    # Verify calibration metrics
    assert "raw_similarity" in results["calibration_metrics"]
    assert "calibrated_platt" in results["calibration_metrics"]

    # Verify fairness audit
    assert "verdict" in results["fairness_audit"]
    assert "trade_parity_ratio" in results["fairness_audit"]

    # Check that empirical status is clearly stated in integrity notice
    assert "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL" in results["integrity_notice"]


# ---------------------------------------------------------------------------
# 10. EvaluationService & API Layer Tests
# ---------------------------------------------------------------------------

def test_evaluation_service_methods():
    """Verify EvaluationService public interface."""
    service = get_evaluation_service()

    # Calibration service
    cal_res = service.calibrate_scores([0.2, 0.4, 0.8, 0.9], [0, 0, 1, 1], method="platt")
    assert "calibrated_probabilities" in cal_res
    assert "improvement_ece" in cal_res

    # Agreement service
    agr_res = service.compute_assessor_agreement(
        metric="cohen_kappa",
        ratings={"rater1": ["A", "B", "A"], "rater2": ["A", "B", "B"]},
    )
    assert "kappa" in agr_res

    # Fairness service
    fair_res = service.audit_fairness([
        {"trade": "electrician", "style": "formal", "extraction_f1": 0.85, "mapping_top1": 1.0, "mapping_mrr": 1.0},
        {"trade": "plumber", "style": "formal", "extraction_f1": 0.80, "mapping_top1": 1.0, "mapping_mrr": 1.0},
    ])
    assert "verdict" in fair_res


def test_api_ground_truth_info(api_client):
    """GET /api/v1/ml/evaluation/ground-truth returns benchmark metadata."""
    resp = api_client.get("/api/v1/ml/evaluation/ground-truth")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset_id"] == "KAUSHALTWIN_BENCHMARK_V1"
    assert data["total_examples"] == 20
    assert data["empirical_status"] == "SYNTHETIC_FIXTURE_PENDING_EMPIRICAL"


def test_api_calibrate_endpoint(api_client):
    """POST /api/v1/ml/evaluation/calibrate computes calibrated probabilities."""
    payload = {
        "scores": [0.1, 0.3, 0.7, 0.9],
        "labels": [0, 0, 1, 1],
        "method": "platt",
        "n_bins": 5,
    }
    resp = api_client.post("/api/v1/ml/evaluation/calibrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "calibrated_probabilities" in data
    assert len(data["calibrated_probabilities"]) == 4
    assert "improvement_ece" in data


def test_api_agreement_endpoint(api_client):
    """POST /api/v1/ml/evaluation/agreement returns agreement metric."""
    payload = {
        "metric": "cohen_kappa",
        "ratings": {
            "rater1": ["Pass", "Fail", "Pass"],
            "rater2": ["Pass", "Fail", "Fail"],
        },
    }
    resp = api_client.post("/api/v1/ml/evaluation/agreement", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "cohen_kappa"
    assert "kappa" in data["result"]


def test_api_fairness_endpoint(api_client):
    """POST /api/v1/ml/evaluation/fairness returns fairness audit report."""
    payload = {
        "records": [
            {"trade": "electrician", "style": "formal", "extraction_f1": 0.90, "mapping_top1": 1.0, "mapping_mrr": 1.0},
            {"trade": "mason", "style": "colloquial", "extraction_f1": 0.80, "mapping_top1": 1.0, "mapping_mrr": 1.0},
        ]
    }
    resp = api_client.post("/api/v1/ml/evaluation/fairness", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert "trade_parity_ratio" in data


def test_api_run_evaluation_endpoint(api_client):
    """POST /api/v1/ml/evaluation/run executes pipeline evaluation."""
    payload = {
        "top_k": 3,
        "min_similarity_threshold": 0.25,
    }
    resp = api_client.post("/api/v1/ml/evaluation/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset_id"] == "KAUSHALTWIN_BENCHMARK_V1"
    assert data["total_examples"] == 20
    assert "extraction_metrics" in data
    assert "mapping_metrics" in data
    assert "calibration_metrics" in data
    assert "fairness_audit" in data
