"""
KaushalTwin Backend — Assessment-to-Certification Complete Workflow Tests
Tests:
1. Candidate onboarding & Assessment creation idempotency
2. Starting assessment (DRAFT -> IN_PROGRESS)
3. Recording practical task observations
4. Assessor recording final certification decision
5. Report and dossier generation with audit trail
"""

import uuid
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase


@pytest.mark.asyncio
async def test_assessment_idempotent_creation(
    client: AsyncClient,
    assessor_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Ensure repeatedly clicking create assessment for the same candidate/trade returns the existing active assessment."""
    worker_id = uuid.uuid4()
    await db.workers.insert_one({
        "id": worker_id,
        "full_name": "Suresh Patel",
        "trade": "Welder",
        "years_of_experience": 5,
    })

    # First creation
    res1 = await client.post(
        "/api/v1/assessments",
        json={"worker_id": str(worker_id), "trade": "Welder"},
        headers=assessor_auth["headers"],
    )
    assert res1.status_code == 201
    asmt1 = res1.json()

    # Second creation with identical parameters
    res2 = await client.post(
        "/api/v1/assessments",
        json={"worker_id": str(worker_id), "trade": "Welder"},
        headers=assessor_auth["headers"],
    )
    assert res2.status_code == 201
    asmt2 = res2.json()

    # IDs must match (resumed, not duplicated)
    assert asmt1["id"] == asmt2["id"]


@pytest.mark.asyncio
async def test_complete_assessment_to_certification_flow(
    client: AsyncClient,
    assessor_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Test full pipeline: Start -> Task Observations -> Assessor Decision -> Dossier Generation."""
    worker_id = uuid.uuid4()
    await db.workers.insert_one({
        "id": worker_id,
        "full_name": "Pooja Sharma",
        "trade": "Solar PV Technician",
        "years_of_experience": 3,
    })

    # 1. Create assessment
    res = await client.post(
        "/api/v1/assessments",
        json={"worker_id": str(worker_id), "trade": "Solar PV Technician"},
        headers=assessor_auth["headers"],
    )
    asmt_id = res.json()["id"]

    # 2. Start assessment
    res_start = await client.post(
        f"/api/v1/assessments/{asmt_id}/start",
        headers=assessor_auth["headers"],
    )
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "IN_PROGRESS"

    # 3. Create practical observation task
    res_task = await client.post(
        f"/api/v1/assessments/{asmt_id}/tasks",
        json={
            "title": "Panel Inverter Connection Test",
            "description": "Assess wiring of microinverter to standard AC breaker.",
            "target_nos_id": "SOL/N0102",
        },
        headers=assessor_auth["headers"],
    )
    assert res_task.status_code == 201
    task_id = res_task.json()["id"]

    # 4. Record assessor observation score
    res_score = await client.post(
        f"/api/v1/assessments/{asmt_id}/tasks/{task_id}/result",
        json={
            "score": 90.0,
            "assessor_comments": "Clean wire stripping and correct terminal torque applied.",
        },
        headers=assessor_auth["headers"],
    )
    assert res_score.status_code == 200
    assert res_score.json()["status"] == "COMPLETED"

    # 5. Assessor records final certification decision
    res_dec = await client.post(
        f"/api/v1/assessments/{asmt_id}/decision",
        json={
            "action": "ACCEPT_RECOMMENDATION",
            "comments": "Candidate demonstrated hands-on mastery of Solar PV installation standards.",
        },
        headers=assessor_auth["headers"],
    )
    assert res_dec.status_code == 201
    dec_data = res_dec.json()
    assert dec_data["action"] == "ACCEPT_RECOMMENDATION"
    assert dec_data["assessor_id"] == str(assessor_auth["user"].id)

    # Assessment status should now be REVIEWED or COMPLETED
    res_asmt = await client.get(
        f"/api/v1/assessments/{asmt_id}",
        headers=assessor_auth["headers"],
    )
    assert res_asmt.json()["status"] in ("REVIEWED", "COMPLETED")

    # 6. Generate official RPL report dossier
    res_rep = await client.get(
        f"/api/v1/assessments/{asmt_id}/report",
        headers=assessor_auth["headers"],
    )
    assert res_rep.status_code == 200
    report = res_rep.json()
    assert report["latest_decision"]["action"] == "ACCEPT_RECOMMENDATION"
    assert report["worker"]["full_name"] == "Pooja Sharma"
