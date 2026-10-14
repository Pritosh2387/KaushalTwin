"""
KaushalTwin ML Service — API: Evaluation, Calibration & Fairness Auditing (Module 10)
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ml.services.evaluation_service import get_evaluation_service
from ml.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    CalibrationRequest,
    CalibrationResponse,
    AgreementRequest,
    AgreementResponse,
    FairnessAuditRequest,
    FairnessAuditResponse,
    BenchmarkInfoResponse,
)

router = APIRouter(prefix="/evaluation", tags=["Evaluation, Calibration & Fairness"])


@router.post(
    "/run",
    response_model=EvaluationRunResponse,
    summary="Run end-to-end evaluation against benchmark suite",
)
def run_evaluation(request: EvaluationRunRequest) -> EvaluationRunResponse:
    """
    Execute full pipeline evaluation against expert ground truth or synthetic benchmark fixtures.
    Computes skill extraction metrics, NOS mapping accuracy, abstention fidelity,
    Platt confidence calibration, and demographic fairness slices.
    """
    try:
        service = get_evaluation_service()
        result = service.run_pipeline_evaluation(
            dataset=request.dataset,
            dataset_path=request.dataset_path,
            top_k=request.top_k,
            min_similarity_threshold=request.min_similarity_threshold,
        )
        return EvaluationRunResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "DATASET_NOT_FOUND", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EVALUATION_RUN_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/calibrate",
    response_model=CalibrationResponse,
    summary="Calibrate raw model confidence into empirical probabilities",
)
def calibrate_scores(request: CalibrationRequest) -> CalibrationResponse:
    """
    Apply statistical calibration (Platt scaling or Isotonic regression) to raw scores.
    Computes pre/post Expected Calibration Error (ECE), MCE, Brier score, and reliability bins.
    """
    try:
        service = get_evaluation_service()
        result = service.calibrate_scores(
            scores=request.scores,
            labels=request.labels,
            method=request.method,
            n_bins=request.n_bins,
        )
        return CalibrationResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "CALIBRATION_VALUE_ERROR", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "CALIBRATION_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/agreement",
    response_model=AgreementResponse,
    summary="Compute inter-rater reliability or AI-assessor alignment",
)
def compute_agreement(request: AgreementRequest) -> AgreementResponse:
    """
    Compute inter-rater reliability across assessors or AI alignment against human consensus.
    Supports Cohen's Kappa, Weighted Kappa, Fleiss' Kappa, Krippendorff's Alpha, and AI alignment.
    """
    try:
        service = get_evaluation_service()
        result = service.compute_assessor_agreement(
            metric=request.metric,
            ratings=request.ratings,
        )
        return AgreementResponse(metric=request.metric, result=result)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "AGREEMENT_INPUT_ERROR", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "AGREEMENT_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/fairness",
    response_model=FairnessAuditResponse,
    summary="Audit demographic and trade fairness disparities",
)
def audit_fairness(request: FairnessAuditRequest) -> FairnessAuditResponse:
    """
    Audit model predictions across trade domains and transcript language styles.
    Computes Trade Parity Ratio, max accuracy disparity, and False Abstention Rate (FAR) disparity.
    """
    try:
        service = get_evaluation_service()
        result = service.audit_fairness(request.records)
        return FairnessAuditResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "FAIRNESS_AUDIT_ERROR", "message": str(exc)}},
        ) from exc


@router.get(
    "/ground-truth",
    response_model=BenchmarkInfoResponse,
    summary="Inspect active benchmark dataset metadata and empirical status",
)
def get_ground_truth_info(
    dataset_path: Optional[str] = Query(default=None, description="Path to custom benchmark JSON")
) -> BenchmarkInfoResponse:
    """
    Retrieve metadata, trade distributions, style breakdown, and provenance integrity notices
    for the active ground-truth benchmark suite.
    """
    try:
        service = get_evaluation_service()
        result = service.get_ground_truth_benchmark_info(path=dataset_path)
        return BenchmarkInfoResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "BENCHMARK_NOT_FOUND", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "BENCHMARK_INFO_ERROR", "message": str(exc)}},
        ) from exc
