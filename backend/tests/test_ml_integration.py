"""
Unit and Integration Tests: ML Service Integration & Persistent AI Results
"""

import json
import uuid
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.services.ml_client import MLServiceError


@pytest.fixture
async def assessment_setup(client: AsyncClient, assessor_auth) -> dict:
    # 1. Create worker
    w_resp = await client.post(
        "/api/v1/workers",
        json={
            "full_name": "Deepak Verma",
            "trade": "electrician",
            "years_of_experience": 6,
            "experience_summary": "6 years doing residential wiring and circuit breaker repairs.",
        },
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    # 2. Create assessment
    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # 3. Add evidence
    await client.post(
        "/api/v1/evidence",
        json={
            "worker_id": worker_id,
            "assessment_id": assessment_id,
            "evidence_type": "SELF_DECLARATION",
            "source_type": "SELF",
            "description": "Candidate self-declaration of 6 years electrical work.",
            "nos_id": "DEMO_NOS_004",
        },
        headers=assessor_auth["headers"],
    )

    return {"worker_id": worker_id, "assessment_id": assessment_id}


@pytest.mark.asyncio
async def test_ml_health_proxy_success(client: AsyncClient):
    with patch("app.api.v1.ml.health_check", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {"status": "ok", "service": "KaushalTwin ML Service"}
        resp = await client.get("/api/v1/ml/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ml_health_proxy_service_unavailable(client: AsyncClient):
    with patch("app.api.v1.ml.health_check", new_callable=AsyncMock) as mock_health:
        mock_health.side_effect = MLServiceError("Connection refused to ML port")
        resp = await client.get("/api/v1/ml/health")
        assert resp.status_code == 503
        assert "ML service unavailable" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_assessment_success(client: AsyncClient, assessor_auth, assessment_setup: dict):
    assessment_id = assessment_setup["assessment_id"]

    mock_ml_response = {
        "worker_id": assessment_setup["worker_id"],
        "preprocessing": {"language": "en", "sentence_count": 1},
        "skills": [{"name": "house wiring", "confidence": 0.95}],
        "nos_candidates": [{"nos_id": "DEMO_NOS_004", "similarity": 0.88}],
        "competency_twin": {
            "worker_id": assessment_setup["worker_id"],
            "competencies": [
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "importance": 1.0,
                    "competency_score": 75,
                    "evidence_coverage": 0.8,
                    "status": "COMPETENT",
                }
            ],
            "summary": {"total_nos": 1},
        },
        "evidence_features": {"conflict": False, "severity": "NONE"},
        "certification_recommendation": {
            "recommendation": "CERTIFY",
            "confidence": 0.85,
            "reasons": ["High competency score and strong evidence coverage"],
        },
        "abstention_decision": {"status": "READY_FOR_ASSESSOR"},
    }

    with patch("app.api.v1.assessments.run_pipeline", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_ml_response

        resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            json={"language": "en"},
            headers=assessor_auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_status"] == "COMPLETED"
        assert data["recommendation"] == "CERTIFY"
        assert data["ml_response"]["skills"][0]["name"] == "house wiring"

        # Check AI runs history
        history_resp = await client.get(
            f"/api/v1/assessments/{assessment_id}/ai-results",
            headers=assessor_auth["headers"],
        )
        assert history_resp.status_code == 200
        runs = history_resp.json()
        assert len(runs) >= 1
        assert runs[0]["recommendation"] == "CERTIFY"


@pytest.mark.asyncio
async def test_analyze_assessment_ml_error_persists_failure(client: AsyncClient, assessor_auth, assessment_setup: dict):
    assessment_id = assessment_setup["assessment_id"]

    with patch("app.api.v1.assessments.run_pipeline", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = MLServiceError("ML worker timeout after 30s")

        resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            json={"language": "en"},
            headers=assessor_auth["headers"],
        )
        assert resp.status_code == 503
        assert "ML service error" in resp.json()["detail"]

        # Confirm failed run was persisted
        history_resp = await client.get(
            f"/api/v1/assessments/{assessment_id}/ai-results",
            headers=assessor_auth["headers"],
        )
        assert history_resp.status_code == 200
        runs = history_resp.json()
        failed_run = next((r for r in runs if r["run_status"] == "FAILED"), None)
        assert failed_run is not None
        assert "ML worker timeout" in failed_run["error_detail"]


@pytest.mark.asyncio
async def test_recommend_next_task_workflow(client: AsyncClient, assessor_auth, assessment_setup: dict):
    assessment_id = assessment_setup["assessment_id"]

    # 1. Before analyze -> next-task should return 422 (no competency data)
    err_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/recommend-next-task",
        headers=assessor_auth["headers"],
    )
    assert err_resp.status_code == 422

    # 2. Run analyze
    mock_ml_response = {
        "competency_twin": {
            "competencies": [
                {
                    "nos_id": "DEMO_NOS_004",
                    "mandatory": True,
                    "importance": 1.0,
                    "competency_score": 60,
                    "evidence_coverage": 0.5,
                }
            ]
        },
        "certification_recommendation": {"recommendation": "REQUEST_MORE_EVIDENCE"},
    }
    with patch("app.api.v1.assessments.run_pipeline", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_ml_response
        await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            json={"language": "en"},
            headers=assessor_auth["headers"],
        )

    # 3. Call recommend-next-task
    mock_task_resp = {
        "selected_task": {
            "id": "TASK_ISOLATION_01",
            "title": "Safe Isolation Practical Demonstration",
            "description": "Isolate circuit safely",
            "duration_minutes": 15,
            "nos_coverage": [{"nos_id": "DEMO_NOS_004", "coverage": 0.9}],
        },
        "priority_score": 0.88,
        "reason": ["High uncertainty in DEMO_NOS_004", "Low duration"],
        "alternatives": [],
        "note": "AI advisory task",
    }
    with patch("app.api.v1.assessments.ml_get_next_task", new_callable=AsyncMock) as mock_nt:
        mock_nt.return_value = mock_task_resp

        resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/recommend-next-task",
            headers=assessor_auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["priority_score"] == 0.88
        assert data["selected_task"]["id"] == "TASK_ISOLATION_01"
        assert data["task_id"] is not None

        # Verify task was persisted as PENDING AI_RECOMMENDED
        task_list_resp = await client.get(
            f"/api/v1/assessments/{assessment_id}/tasks",
            headers=assessor_auth["headers"],
        )
        assert task_list_resp.status_code == 200
        tasks = task_list_resp.json()
        recommended = next((t for t in tasks if t["ml_task_id"] == "TASK_ISOLATION_01"), None)
        assert recommended is not None
        assert recommended["selection_source"] == "AI_RECOMMENDED"
        assert recommended["status"] == "PENDING"


@pytest.mark.asyncio
async def test_check_evidence_endpoint(client: AsyncClient, assessor_auth, assessment_setup: dict):
    assessment_id = assessment_setup["assessment_id"]

    with patch("app.api.v1.assessments.ml_analyze_evidence", new_callable=AsyncMock) as mock_ev, \
         patch("app.api.v1.assessments.ml_check_abstention", new_callable=AsyncMock) as mock_abs:

        mock_ev.return_value = {"conflict": False, "severity": "NONE", "reason": "No conflicting evidence"}
        mock_abs.return_value = {"status": "READY_FOR_ASSESSOR", "confidence": 0.9}

        resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/check-evidence",
            headers=assessor_auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "evidence_analysis" in data
        assert data["evidence_analysis"]["conflict"] is False
        assert data["abstention_check"]["status"] == "READY_FOR_ASSESSOR"
        assert "ai_run_id" in data
