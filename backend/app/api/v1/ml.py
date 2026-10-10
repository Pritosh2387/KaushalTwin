"""
KaushalTwin Backend — API Routes: ML Service Proxy / Health

GET  /api/v1/ml/health  — Proxy health check to the ML service
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.services.ml_client import health_check, MLServiceError

router = APIRouter(prefix="/ml", tags=["ML Service"])


@router.get(
    "/health",
    summary="Check ML service health",
)
async def ml_health() -> dict:
    """
    Proxy liveness check to the KaushalTwin ML service.
    Returns 503 if the ML service is unreachable.
    """
    try:
        return await health_check()
    except MLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service unavailable: {exc}",
        )
