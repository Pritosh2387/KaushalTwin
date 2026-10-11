"""
Unit and Integration Tests: Assessor Final Decision & Independence from AI
"""

import uuid
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.db.models.user import UserRole


@pytest.fixture
async def setup_with_ai_run(client: AsyncClient, assessor_auth) -> dict:
    # 1. Create worker
    w_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Decision Test Worker", "trade": "electrician", "years_of_experience": 5},
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    # 2. Create assessment & start it
    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]
    await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])

    # 3. Simulate completed AI run
    mock_ml = {
        "certification_recommendation": {
            "recommendation": "CERTIFY",
            "confidence": 0.88,
            "reasons": ["Passed all core standards"],
        },
        "competency_twin": {"competencies": []},
    }
    with patch("app.api.v1.assessments.run_pipeline", new_callable=AsyncMock) as mock_p:
        mock_p.return_value = mock_ml
        ai_resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            json={"language": "en"},
            headers=assessor_auth["headers"],
        )
        ai_run_id = ai_resp.json()["id"]

    return {"worker_id": worker_id, "assessment_id": assessment_id, "ai_run_id": ai_run_id}


@pytest.mark.asyncio
async def test_get_recommendation_endpoint(client: AsyncClient, assessor_auth, setup_with_ai_run: dict):
    assessment_id = setup_with_ai_run["assessment_id"]
    resp = await client.get(
        f"/api/v1/assessments/{assessment_id}/recommendation",
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendation"] == "CERTIFY"
    assert "human assessor makes the final decision" in data["note"]


@pytest.mark.asyncio
async def test_assessor_accepts_recommendation(client: AsyncClient, assessor_auth, setup_with_ai_run: dict):
    assessment_id = setup_with_ai_run["assessment_id"]
    ai_run_id = setup_with_ai_run["ai_run_id"]

    decision_payload = {
        "action": "ACCEPT_RECOMMENDATION",
        "ai_run_id": ai_run_id,
        "comments": "Agreed with AI analysis. Candidate exhibited solid safety protocols.",
    }
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json=decision_payload,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["action"] == "ACCEPT_RECOMMENDATION"
    assert data["comments"] == decision_payload["comments"]
    assert data["ai_run_id"] == ai_run_id

    # Verify assessment transitioned to REVIEWED
    a_resp = await client.get(f"/api/v1/assessments/{assessment_id}", headers=assessor_auth["headers"])
    assert a_resp.json()["status"] == "REVIEWED"


@pytest.mark.asyncio
async def test_assessor_rejects_recommendation_preserves_ai_run(
    client: AsyncClient, assessor_auth, setup_with_ai_run: dict
):
    """
    CRITICAL SIH RULE: Assessor can disagree with AI without overwriting the historical AI run.
    """
    assessment_id = setup_with_ai_run["assessment_id"]
    ai_run_id = setup_with_ai_run["ai_run_id"]

    decision_payload = {
        "action": "REJECT_RECOMMENDATION",
        "ai_run_id": ai_run_id,
        "comments": "Observed severe safety violation during practical task not captured by AI.",
    }
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json=decision_payload,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 201
    assert resp.json()["action"] == "REJECT_RECOMMENDATION"

    # Verify AI recommendation in AIAssessmentRun remains intact as CERTIFY
    ai_runs_resp = await client.get(
        f"/api/v1/assessments/{assessment_id}/ai-results",
        headers=assessor_auth["headers"],
    )
    assert ai_runs_resp.status_code == 200
    runs = ai_runs_resp.json()
    target_run = next((r for r in runs if r["id"] == ai_run_id), None)
    assert target_run is not None
    assert target_run["recommendation"] == "CERTIFY"  # Immutable AI recommendation preserved!


@pytest.mark.asyncio
async def test_assessor_requests_more_evidence(client: AsyncClient, assessor_auth, setup_with_ai_run: dict):
    assessment_id = setup_with_ai_run["assessment_id"]
    decision_payload = {
        "action": "REQUEST_MORE_EVIDENCE",
        "comments": "Need employer verification letter before certifying.",
    }
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json=decision_payload,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 201
    assert resp.json()["action"] == "REQUEST_MORE_EVIDENCE"


@pytest.mark.asyncio
async def test_assessor_modifies_recommendation(client: AsyncClient, assessor_auth, setup_with_ai_run: dict):
    assessment_id = setup_with_ai_run["assessment_id"]
    decision_payload = {
        "action": "MODIFY_RECOMMENDATION",
        "modified_recommendation": "PARTIAL_CERTIFICATION",
        "comments": "Candidate certified only for low-voltage residential wiring.",
    }
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json=decision_payload,
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 201
    assert resp.json()["action"] == "MODIFY_RECOMMENDATION"
    assert resp.json()["modified_recommendation"] == "PARTIAL_CERTIFICATION"


@pytest.mark.asyncio
async def test_worker_cannot_submit_decision(client: AsyncClient, worker_auth, setup_with_ai_run: dict):
    assessment_id = setup_with_ai_run["assessment_id"]
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"action": "ACCEPT_RECOMMENDATION"},
        headers=worker_auth["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthorized_assessor_cannot_submit_decision(
    client: AsyncClient, create_user, setup_with_ai_run: dict
):
    assessment_id = setup_with_ai_run["assessment_id"]
    other_assessor, other_token = await create_user(
        "Other Assessor", "assessor_intruder@example.com", role=UserRole.ASSESSOR
    )
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"action": "ACCEPT_RECOMMENDATION"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
