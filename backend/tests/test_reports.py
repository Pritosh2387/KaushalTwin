"""
Unit and Integration Tests: Structured Report Generation & Audit Trail APIs
"""

import uuid
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.db.models.user import UserRole


@pytest.mark.asyncio
async def test_generate_structured_report(client: AsyncClient, assessor_auth):
    # 1. Create worker
    w_resp = await client.post(
        "/api/v1/workers",
        json={
            "full_name": "Rohan Gupta",
            "trade": "electrician",
            "years_of_experience": 7,
            "experience_summary": "7 years experienced wireman",
        },
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    # 2. Create assessment
    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "electrician", "notes": "Full RPL evaluation"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # 3. Add evidence and verify
    ev_resp = await client.post(
        "/api/v1/evidence",
        json={
            "worker_id": worker_id,
            "assessment_id": assessment_id,
            "evidence_type": "CERTIFICATE",
            "source_type": "EMPLOYER",
            "description": "NASSCOM Certificate",
            "nos_id": "DEMO_NOS_004",
        },
        headers=assessor_auth["headers"],
    )
    ev_id = ev_resp.json()["id"]
    await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={"verification_status": "VERIFIED", "verification_notes": "Verified"},
        headers=assessor_auth["headers"],
    )

    # 4. Add task & complete
    t_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks",
        json={"title": "Practical Test 1", "target_nos_id": "DEMO_NOS_004"},
        headers=assessor_auth["headers"],
    )
    task_id = t_resp.json()["id"]
    await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks/{task_id}/result",
        json={"score": 90.0, "assessor_comments": "Excellent"},
        headers=assessor_auth["headers"],
    )

    # 5. Run AI analysis
    mock_ml = {
        "certification_recommendation": {
            "recommendation": "CERTIFY",
            "confidence": 0.92,
            "reasons": ["All standards achieved"],
        },
        "competency_twin": {
            "competencies": [{"nos_id": "DEMO_NOS_004", "competency_score": 90, "evidence_coverage": 1.0}]
        },
        "skill_gap_analysis": {"gap_count": 0},
        "abstention_decision": {"status": "READY_FOR_ASSESSOR"},
    }
    with patch("app.api.v1.assessments.run_pipeline", new_callable=AsyncMock) as mock_p:
        mock_p.return_value = mock_ml
        ai_run_resp = await client.post(
            f"/api/v1/assessments/{assessment_id}/analyze",
            json={"language": "en"},
            headers=assessor_auth["headers"],
        )
        ai_run_id = ai_run_resp.json()["id"]

    # 6. Assessor submits decision
    await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json={"action": "ACCEPT_RECOMMENDATION", "ai_run_id": ai_run_id, "comments": "Final pass"},
        headers=assessor_auth["headers"],
    )

    # 7. Generate report
    report_resp = await client.get(
        f"/api/v1/assessments/{assessment_id}/report",
        headers=assessor_auth["headers"],
    )
    assert report_resp.status_code == 200
    report = report_resp.json()

    # Verify report sections
    assert "generated_at" in report
    assert report["worker"]["full_name"] == "Rohan Gupta"
    assert report["worker"]["years_of_experience"] == 7
    assert report["assessment"]["trade"] == "electrician"

    # Evidence section
    assert report["evidence_summary"]["total"] == 1
    assert report["evidence_summary"]["verified"] == 1

    # Tasks section
    assert len(report["tasks"]) == 1
    assert report["tasks"][0]["score"] == 90.0

    # AI runs & recommendation
    assert len(report["ai_runs"]) == 1
    assert report["latest_recommendation"]["recommendation"] == "CERTIFY"

    # Final decision
    assert report["latest_decision"]["action"] == "ACCEPT_RECOMMENDATION"
    assert report["latest_decision"]["comments"] == "Final pass"

    # Audit timeline
    assert len(report["audit_timeline"]) >= 3
    # Every audit event has an action and actor
    for event in report["audit_timeline"]:
        assert "action" in event
        assert "actor" in event
        assert "timestamp" in event


@pytest.mark.asyncio
async def test_report_access_denied_for_other_worker(client: AsyncClient, assessor_auth, create_user):
    # Assessor creates assessment
    w_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Worker Secret", "trade": "electrician", "years_of_experience": 2},
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # Unrelated worker tries to access report -> 403 Forbidden
    other_worker, other_token = await create_user("Intruder Worker", "intruder@example.com", role=UserRole.WORKER)
    resp = await client.get(
        f"/api/v1/assessments/{assessment_id}/report",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
