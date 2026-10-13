"""
KaushalTwin ML Service — Preprocessing API
Module 1: Data Ingestion & ML Preprocessing
"""

from fastapi import APIRouter, HTTPException
from ml.schemas.preprocessing import PreprocessRequest, PreprocessResponse
from ml.services.preprocessing_service import preprocess_text

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
        return preprocess_text(
            request.text,
            language=request.language,
            lowercase=request.lowercase,
        )
    except InvalidInputError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": exc.error_code, "message": exc.message}},
        ) from exc
    except ValueError as exc:
        # Keep ValueError handling for backward compatibility
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(exc)}},
        ) from exc
