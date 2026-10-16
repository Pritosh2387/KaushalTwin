"""
KaushalTwin Backend — Comprehensive Audit Trail & Hash-Chain Integrity Tests
Tests:
1. Event persistence and SHA-256 hash chaining
2. Verification endpoint GET /api/v1/audit/verify
3. Tamper detection on modified payload
4. Role-based access control (Worker 403, Assessor 200)
5. Audit event filtering and search
"""

import uuid
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.audit_service import (
    record_event,
    verify_audit_log_integrity,
    GENESIS_HASH,
)


@pytest.mark.asyncio
async def test_audit_event_hash_chaining(db: AsyncIOMotorDatabase):
    """Verify that successive audit events form a continuous SHA-256 hash chain."""
    actor_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    ev1 = await record_event(
        db,
        action="EVIDENCE_SUBMITTED",
        entity_type="EVIDENCE",
        entity_id=str(resource_id),
        actor_user_id=actor_id,
        actor_role="WORKER",
        metadata={"detail": "Initial work sample submitted"},
    )
    assert ev1["prev_hash"] == GENESIS_HASH
    assert ev1["integrity_hash"] is not None
    assert len(ev1["integrity_hash"]) == 64

    ev2 = await record_event(
        db,
        action="EVIDENCE_VERIFIED",
        entity_type="EVIDENCE",
        entity_id=str(resource_id),
        actor_user_id=actor_id,
        actor_role="ASSESSOR",
        metadata={"decision": "VERIFIED"},
    )
    assert ev2["prev_hash"] == ev1["integrity_hash"]
    assert ev2["integrity_hash"] is not None

    verification = await verify_audit_log_integrity(db)
    assert verification["is_valid"] is True
    assert verification["verified_events"] == 2
    assert verification["corrupted_events"] == 0
    assert verification["broken_links"] == 0


@pytest.mark.asyncio
async def test_audit_tamper_detection(db: AsyncIOMotorDatabase):
    """Verify that tampering with an audit record in the database is detected by verification."""
    actor_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    ev1 = await record_event(
        db,
        action="ASSESSMENT_CREATED",
        entity_type="ASSESSMENT",
        entity_id=str(resource_id),
        actor_user_id=actor_id,
        actor_role="ASSESSOR",
    )
    ev2 = await record_event(
        db,
        action="ASSESSOR_DECISION_RECORDED",
        entity_type="ASSESSMENT",
        entity_id=str(resource_id),
        actor_user_id=actor_id,
        actor_role="ASSESSOR",
    )

    # Tamper directly with the first event in MongoDB
    await db.audit_events.update_one(
        {"id": ev1["id"]},
        {"$set": {"action": "TAMPERED_ACTION_FORGED"}}
    )

    # Re-verify integrity
    verification = await verify_audit_log_integrity(db)
    assert verification["is_valid"] is False
    assert verification["corrupted_events"] >= 1
    assert verification["errors"][0]["event_id"] == str(ev1["id"])
    assert verification["errors"][0]["error_type"] == "HASH_MISMATCH_TAMPERED"


@pytest.mark.asyncio
async def test_audit_api_endpoints(
    client: AsyncClient,
    assessor_auth: dict,
    worker_auth: dict,
    db: AsyncIOMotorDatabase,
):
    """Test API access, authorization, and output format for audit endpoints."""
    # Write a test event
    await record_event(
        db,
        action="AI_ANALYSIS_EXECUTED",
        entity_type="ASSESSMENT",
        entity_id=str(uuid.uuid4()),
        actor_user_id=assessor_auth["user"].id,
        actor_role="ASSESSOR",
    )

    # Assessor can access audit events
    res = await client.get("/api/v1/audit/events", headers=assessor_auth["headers"])
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1

    # Assessor can verify integrity
    verify_res = await client.get("/api/v1/audit/verify", headers=assessor_auth["headers"])
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert "guarantee" in verify_data

    # Worker role is forbidden from viewing audit ledger
    worker_res = await client.get("/api/v1/audit/events", headers=worker_auth["headers"])
    assert worker_res.status_code == 403

    worker_verify = await client.get("/api/v1/audit/verify", headers=worker_auth["headers"])
    assert worker_verify.status_code == 403
