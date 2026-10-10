"""
KaushalTwin Backend — ML Service Client

Async HTTPX client for calling the existing KaushalTwin ML service.

Rules:
- Base URL comes from settings.ML_SERVICE_URL (never hard-coded)
- Every call has an explicit timeout
- HTTP errors, connection errors, and invalid responses are caught and
  re-raised as MLServiceError (never silently discarded)
- No ML results are fabricated on error — callers receive a clear error
- The client is reused across requests (lifespan-managed)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MLServiceError(Exception):
    """Raised when the ML service is unavailable or returns an unexpected response."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Shared async client (managed in app lifespan)
# ---------------------------------------------------------------------------

_client: Optional[httpx.AsyncClient] = None


def get_ml_client() -> httpx.AsyncClient:
    """Return the shared HTTPX client. Must be initialized before use."""
    if _client is None:
        raise RuntimeError("ML client not initialized. Call init_ml_client() first.")
    return _client


async def init_ml_client() -> None:
    """Create the shared async client. Call once at app startup."""
    global _client
    _client = httpx.AsyncClient(
        base_url=settings.ML_SERVICE_URL,
        timeout=httpx.Timeout(settings.ML_SERVICE_TIMEOUT),
    )
    logger.info("ML service client initialized: %s", settings.ML_SERVICE_URL)


async def close_ml_client() -> None:
    """Close the shared client. Call once at app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("ML service client closed")


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

async def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    POST to the ML service and return the parsed JSON response.

    Raises MLServiceError on:
    - Connection failure / timeout
    - Non-2xx HTTP response
    - Non-JSON / unexpected response body
    """
    client = get_ml_client()
    try:
        response = await client.post(path, json=payload)
    except httpx.TimeoutException as exc:
        raise MLServiceError(
            f"ML service timed out after {settings.ML_SERVICE_TIMEOUT}s: {path}"
        ) from exc
    except httpx.RequestError as exc:
        raise MLServiceError(
            f"ML service unreachable at {settings.ML_SERVICE_URL}{path}: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise MLServiceError(
            f"ML service returned {response.status_code} for {path}: {detail}",
            status_code=response.status_code,
        )

    try:
        return response.json()
    except Exception as exc:
        raise MLServiceError(
            f"ML service returned non-JSON response for {path}"
        ) from exc


async def _get(path: str) -> dict[str, Any]:
    client = get_ml_client()
    try:
        response = await client.get(path)
    except httpx.TimeoutException as exc:
        raise MLServiceError(f"ML service timed out: {path}") from exc
    except httpx.RequestError as exc:
        raise MLServiceError(f"ML service unreachable: {exc}") from exc

    if response.status_code >= 400:
        raise MLServiceError(
            f"ML service returned {response.status_code} for {path}",
            status_code=response.status_code,
        )

    return response.json()


# ---------------------------------------------------------------------------
# Public API — one method per ML endpoint
# ---------------------------------------------------------------------------

async def health_check() -> dict:
    """GET /health — liveness probe for the ML service."""
    return await _get("/health")


async def preprocess_text(text: str, language: str = "en") -> dict:
    """POST /api/v1/ml/preprocess/text"""
    return await _post(
        "/api/v1/ml/preprocess/text",
        {"text": text, "language": language},
    )


async def extract_skills(text: str, language: str = "en", trade: str = "electrician") -> dict:
    """POST /api/v1/ml/skills/extract"""
    return await _post(
        "/api/v1/ml/skills/extract",
        {"text": text, "language": language, "trade": trade, "provider": "demo"},
    )


async def map_skills_to_nos(skills: list[dict], top_k: int = 3) -> dict:
    """POST /api/v1/ml/nos/map"""
    return await _post(
        "/api/v1/ml/nos/map",
        {"skills": skills, "top_k": top_k, "embedding_provider": "demo"},
    )


async def score_competency(competency: dict) -> dict:
    """POST /api/v1/ml/competency/score"""
    return await _post("/api/v1/ml/competency/score", competency)


async def build_competency_twin(worker_id: str, competencies: list[dict]) -> dict:
    """POST /api/v1/ml/competency/twin"""
    return await _post(
        "/api/v1/ml/competency/twin",
        {"worker_id": worker_id, "competencies": competencies},
    )


async def analyze_evidence(evidence: list[dict]) -> dict:
    """POST /api/v1/ml/evidence/analyze"""
    return await _post("/api/v1/ml/evidence/analyze", {"evidence": evidence})


async def get_next_task(
    competency_states: list[dict],
    exclude_task_ids: Optional[list[str]] = None,
) -> dict:
    """POST /api/v1/ml/assessment/next-task"""
    payload: dict = {"competency_states": competency_states}
    if exclude_task_ids:
        payload["exclude_task_ids"] = exclude_task_ids
    return await _post("/api/v1/ml/assessment/next-task", payload)


async def analyze_skill_gap(
    worker_id: str,
    competencies: list[dict],
    evidence_records: Optional[list[dict]] = None,
) -> dict:
    """POST /api/v1/ml/skill-gap/analyze"""
    payload: dict = {"worker_id": worker_id, "competencies": competencies}
    if evidence_records:
        payload["evidence_records"] = evidence_records
    return await _post("/api/v1/ml/skill-gap/analyze", payload)


async def check_abstention(
    worker_id: str,
    competencies: list[dict],
    evidence_records: Optional[list[dict]] = None,
) -> dict:
    """POST /api/v1/ml/abstention/check"""
    payload: dict = {"worker_id": worker_id, "competencies": competencies}
    if evidence_records:
        payload["evidence_records"] = evidence_records
    return await _post("/api/v1/ml/abstention/check", payload)


async def recommend_certification(
    worker_id: str,
    competency_profile: list[dict],
    skill_gap_analysis: Optional[dict] = None,
    abstention_decision: Optional[dict] = None,
    calibration_info: Optional[dict] = None,
) -> dict:
    """POST /api/v1/ml/certification/recommend"""
    payload: dict = {
        "worker_id": worker_id,
        "competency_profile": competency_profile,
    }
    if skill_gap_analysis:
        payload["skill_gap_analysis"] = skill_gap_analysis
    if abstention_decision:
        payload["abstention_decision"] = abstention_decision
    if calibration_info:
        payload["calibration_info"] = calibration_info
    return await _post("/api/v1/ml/certification/recommend", payload)


async def run_pipeline(
    worker_id: str,
    transcript: str,
    language: str = "en",
    trade: str = "electrician",
    competencies: Optional[list[dict]] = None,
    evidence: Optional[list[dict]] = None,
    assessor_scores: Optional[list[dict]] = None,
    claim: Optional[str] = None,
    top_k_nos: int = 3,
) -> dict:
    """POST /api/v1/ml/pipeline/worker-assessment — unified full pipeline."""
    payload: dict = {
        "worker_id": worker_id,
        "transcript": transcript,
        "language": language,
        "trade": trade,
        "competencies": competencies or [],
        "evidence": evidence or [],
        "top_k_nos": top_k_nos,
    }
    if assessor_scores:
        payload["assessor_scores"] = assessor_scores
    if claim:
        payload["claim"] = claim
    return await _post("/api/v1/ml/pipeline/worker-assessment", payload)
