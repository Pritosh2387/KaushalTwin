"""
Unit and Integration Tests: Assessment Lifecycle & Tasks APIs
"""

import uuid
import pytest
from httpx import AsyncClient

from app.db.models.user import UserRole


@pytest.fixture
async def sample_worker_id(client: AsyncClient, assessor_auth) -> str:
    resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Assessment Test Worker", "trade": "electrician", "years_of_experience": 4},
        headers=assessor_auth["headers"],
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_assessment_creation_and_lifecycle(client: AsyncClient, assessor_auth, sample_worker_id: str):
    # 1. Create assessment
    payload = {
        "worker_id": sample_worker_id,
        "trade": "electrician",
        "notes": "Initial candidate interview planned",
    }
    create_resp = await client.post("/api/v1/assessments", json=payload, headers=assessor_auth["headers"])
    assert create_resp.status_code == 201
    assessment = create_resp.json()
    assert assessment["status"] == "DRAFT"
    assessment_id = assessment["id"]

    # 2. Start assessment: DRAFT -> IN_PROGRESS
    start_resp = await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "IN_PROGRESS"
    assert start_resp.json()["started_at"] is not None

    # Cannot re-start already started assessment
    restart_resp = await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])
    assert restart_resp.status_code == 409

    # 3. Complete assessment: IN_PROGRESS -> READY_FOR_REVIEW
    complete_resp = await client.post(f"/api/v1/assessments/{assessment_id}/complete", headers=assessor_auth["headers"])
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "READY_FOR_REVIEW"
    assert complete_resp.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_cannot_complete_draft_assessment(client: AsyncClient, assessor_auth, sample_worker_id: str):
    create_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": sample_worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = create_resp.json()["id"]

    # Attempt to complete without starting
    complete_resp = await client.post(f"/api/v1/assessments/{assessment_id}/complete", headers=assessor_auth["headers"])
    assert complete_resp.status_code == 409


@pytest.mark.asyncio
async def test_task_management_and_scoring(client: AsyncClient, assessor_auth, sample_worker_id: str):
    create_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": sample_worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = create_resp.json()["id"]
    await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])

    # Add a task
    task_payload = {
        "title": "Demonstrate Safe Isolation Procedure",
        "description": "Candidate must safely isolate DB board and test with multimeter",
        "target_nos_id": "DEMO_NOS_004",
        "selection_source": "ASSESSOR_ASSIGNED",
    }
    task_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks",
        json=task_payload,
        headers=assessor_auth["headers"],
    )
    assert task_resp.status_code == 201
    task = task_resp.json()
    assert task["status"] == "PENDING"
    assert task["selection_source"] == "ASSESSOR_ASSIGNED"
    task_id = task["id"]

    # List tasks
    list_resp = await client.get(f"/api/v1/assessments/{assessment_id}/tasks", headers=assessor_auth["headers"])
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Submit task result
    result_payload = {
        "score": 85.0,
        "assessor_comments": "Good technique; properly checked meter on proving unit first.",
        "evidence_references": ["ev-101", "ev-102"],
    }
    score_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks/{task_id}/result",
        json=result_payload,
        headers=assessor_auth["headers"],
    )
    assert score_resp.status_code == 200
    scored = score_resp.json()
    assert scored["status"] == "COMPLETED"
    assert scored["score"] == 85.0
    assert scored["completed_at"] is not None

    # Cannot resubmit completed task
    resubmit_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks/{task_id}/result",
        json=result_payload,
        headers=assessor_auth["headers"],
    )
    assert resubmit_resp.status_code == 409


@pytest.mark.asyncio
async def test_other_assessor_cannot_modify(client: AsyncClient, assessor_auth, create_user, sample_worker_id: str):
    create_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": sample_worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = create_resp.json()["id"]

    # Another assessor
    other_assessor, other_token = await create_user(
        "Other Assessor", "other_assessor@example.com", role=UserRole.ASSESSOR
    )

    # Attempt to start -> 403 Forbidden
    resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/start",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
