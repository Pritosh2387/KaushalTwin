"""
KaushalTwin ML Service — Evidence API
Module 4: Evidence Feature & Integrity Support
"""

import base64

from fastapi import APIRouter, HTTPException
from app.schemas.evidence import (
    EvidenceAnalysisRequest,
    EvidenceAnalysisResponse,
    EvidenceConflictRequest,
    EvidenceConflictResponse,
    EvidenceHashRequest,
    EvidenceHashResponse,
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    SourceFeature,
)
from app.services.evidence_service import (
    analyse_evidence,
    detect_conflict,
    hash_content,
    check_duplicates,
)

router = APIRouter(prefix="/evidence", tags=["Module 4 · Evidence & Integrity"])


@router.post(
    "/analyze",
    response_model=EvidenceAnalysisResponse,
    summary="Analyse evidence records and extract reliability features",
)
def analyse_evidence_endpoint(request: EvidenceAnalysisRequest) -> EvidenceAnalysisResponse:
    """
    Extract features from a set of evidence records.

    Source weights are configurable prototype values — not empirically validated.
    """
    evidence_raw = [e.model_dump() for e in request.evidence]
    result = analyse_evidence(evidence_raw, request.custom_weights)
    return EvidenceAnalysisResponse(
        source_features=[SourceFeature(**f) for f in result["source_features"]],
        support_score=result["support_score"],
        contradict_score=result["contradict_score"],
        independent_sources=result["independent_sources"],
        conflict=result["conflict"],
        conflict_reason=result.get("conflict_reason"),
    )


@router.post(
    "/conflict",
    response_model=EvidenceConflictResponse,
    summary="Detect conflicts between evidence records",
)
def detect_conflict_endpoint(request: EvidenceConflictRequest) -> EvidenceConflictResponse:
    """
    Detect if self-declaration conflicts with practical evidence.

    HIGH: self-declaration supported + practical contradicts.
    MEDIUM: both supporting and contradicting high-weight evidence.
    LOW: minor contradiction.
    """
    evidence_raw = [e.model_dump() for e in request.evidence]
    result = detect_conflict(evidence_raw, request.custom_weights)
    return EvidenceConflictResponse(**result)


@router.post(
    "/hash",
    response_model=EvidenceHashResponse,
    summary="Calculate SHA-256 hash for file integrity",
)
def hash_evidence_endpoint(request: EvidenceHashRequest) -> EvidenceHashResponse:
    """
    Calculate SHA-256 hash for a base64-encoded file/content.

    This verifies file integrity only — it does NOT prove evidence authenticity.
    """
    try:
        content = base64.b64decode(request.content_base64)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_BASE64", "message": "content_base64 is not valid base64"}},
        ) from exc
    result = hash_content(content)
    return EvidenceHashResponse(**result)


@router.post(
    "/duplicates",
    response_model=DuplicateCheckResponse,
    summary="Detect exact SHA-256 duplicate hashes",
)
def check_duplicates_endpoint(request: DuplicateCheckRequest) -> DuplicateCheckResponse:
    """
    Find groups of identical SHA-256 hashes.
    Exact match only — perceptual/video duplicate detection is a future feature.
    """
    result = check_duplicates(request.hashes)
    return DuplicateCheckResponse(**result)
