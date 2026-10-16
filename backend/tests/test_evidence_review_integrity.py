"""
KaushalTwin Backend — Evidence Verification and Review Integrity Tests
Tests:
1. Submissions are not automatically verified (UNVERIFIED / PENDING_REVIEW)
2. Role enforcement: Worker cannot verify evidence (403)
3. Assessor verification records reviewer ID, timestamp, and audit event
4. Rejection leaves evidence visible with status and feedback
5. Validation rejects invalid status values
"""

import uuid
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase


@pytest.mark.asyncio
async def test_evidence_submission_not_automatically_verified(
    client: AsyncClient,
    worker_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Ensure worker evidence submissions start in UNVERIFIED/PENDING_REVIEW, never automatically VERIFIED."""
    # Create worker record
    worker_doc = {
        "id": uuid.uuid4(),
        "user_id": worker_auth["user"].id,
        "full_name": "Test Worker",
        "trade": "Electrical Installation",
        "years_of_experience": 4,
    }
    await db.workers.insert_one(worker_doc)

    res = await client.post(
        "/api/v1/evidence",
        json={
            "worker_id": str(worker_doc["id"]),
            "evidence_type": "SELF_DECLARATION",
            "source_type": "SELF",
            "description": "Unverified self declaration of skills",
            "nos_id": "ELE/N5801",
        },
        headers=worker_auth["headers"],
    )
    assert res.status_code == 201
    ev_data = res.json()
    assert ev_data["verification_status"] in ("UNVERIFIED", "PENDING_REVIEW", "PENDING")
    assert ev_data["verification_status"] != "VERIFIED"
    assert ev_data.get("verified_by_id") is None
    assert ev_data.get("verified_at") is None


@pytest.mark.asyncio
async def test_worker_cannot_verify_evidence(
    client: AsyncClient,
    worker_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Enforce authorization: workers are forbidden from verifying evidence."""
    ev_id = uuid.uuid4()
    await db.evidence.insert_one({
        "id": ev_id,
        "worker_id": uuid.uuid4(),
        "evidence_type": "WORK_SAMPLE",
        "description": "Sample test piece",
        "verification_status": "PENDING_REVIEW",
    })

    res = await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={
            "verification_status": "VERIFIED",
            "verification_notes": "Attempting self verification",
        },
        headers=worker_auth["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_assessor_verification_records_attribution_and_audit(
    client: AsyncClient,
    assessor_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Assessor verification records authenticated reviewer ID, timestamp, and audit event."""
    ev_id = uuid.uuid4()
    worker_id = uuid.uuid4()
    await db.evidence.insert_one({
        "id": ev_id,
        "worker_id": worker_id,
        "evidence_type": "PHOTOGRAPH",
        "description": "Onsite safety gear photo",
        "verification_status": "PENDING_REVIEW",
    })

    res = await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={
            "verification_status": "VERIFIED",
            "verification_notes": "PPE standards verified per ISO 45001.",
        },
        headers=assessor_auth["headers"],
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["verification_status"] == "VERIFIED"
    assert updated["verified_by_id"] == str(assessor_auth["user"].id)
    assert updated["verified_at"] is not None

    # Check that audit ledger recorded this verification action in audit_events
    audit_event = await db.audit_events.find_one({
        "entity_id": str(ev_id),
        "action": "EVIDENCE_VERIFIED",
    })
    assert audit_event is not None
    assert audit_event["actor_role"] == "ASSESSOR"
    assert audit_event["actor_user_id"] == str(assessor_auth["user"].id)


@pytest.mark.asyncio
async def test_assessor_can_reject_evidence_with_notes(
    client: AsyncClient,
    assessor_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Assessor can reject evidence, leaving rejection notes visible."""
    ev_id = uuid.uuid4()
    await db.evidence.insert_one({
        "id": ev_id,
        "worker_id": uuid.uuid4(),
        "evidence_type": "CERTIFICATE",
        "description": "Unclear course certificate",
        "verification_status": "PENDING_REVIEW",
    })

    res = await client.post(
        f"/api/v1/evidence/{ev_id}/verify",
        json={
            "verification_status": "REJECTED",
            "verification_notes": "Certificate issuer not accredited under NCVET.",
        },
        headers=assessor_auth["headers"],
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["verification_status"] == "REJECTED"
    assert updated["verification_notes"] == "Certificate issuer not accredited under NCVET."
