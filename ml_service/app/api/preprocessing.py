"""
KaushalTwin ML Service — Preprocessing API
Module 1: Data Ingestion & ML Preprocessing
"""

from fastapi import APIRouter, HTTPException
from app.schemas.preprocessing import PreprocessRequest, PreprocessResponse
from app.services.preprocessing_service import preprocess_text

router = APIRouter(prefix="/preprocess", tags=["Module 1 · Preprocessing"])


@router.post("/text", response_model=PreprocessResponse, summary="Preprocess raw transcript text")
def preprocess_text_endpoint(request: PreprocessRequest) -> PreprocessResponse:
    """
    Normalise and tokenise a raw worker transcript.

    - Preserves original text alongside normalised version.
    - Detects or accepts declared language.
    - Splits into sentences and tokens.
    """
    try:
        result = preprocess_text(
            request.text,
            language=request.language,
            lowercase=request.lowercase,
        )
        return PreprocessResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(exc)}},
        ) from exc
