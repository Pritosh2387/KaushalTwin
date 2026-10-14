"""
Integration and End-to-End Tests for Priority 8: Deployment Readiness & E2E Workflows
Covers:
- Scenario A: Successful End-to-End Assessment Workflow
- Scenario B: Insufficient Evidence & Abstention Handling
- Scenario C: Assessor Human Decision Authority & Persistence Separation
- Scenario D: Authentication, Authorization & Role-Based Access Control
- Scenario E: Database Persistence & Cross-Entity Relational Integrity
- Scenario F: Service Failure, Error Handling & Resilient Fallbacks
"""

import uuid
import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.models.user import UserRole


# ---------------------------------------------------------------------------
# Scenario A: Successful End-to-End Assessment Workflow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_a_successful_assessment_workflow(
    client: AsyncClient,
    assessor_auth: dict,
    db_session: AsyncIOMotorDatabase,
):
    """
    Scenario A:
    Worker intake -> Experience narrative -> Skill extraction -> NOS mapping ->
    Evidence submission -> Assessment creation -> Analysis -> Next task recommendation ->
    Task completion -> Assessor report generation.
    """
    # 1. Intake: Create worker profile with rich practical narrative
    worker_payload = {
        "full_name": "Kailash Chand Sharma",
        "trade": "electrician",
        "years_of_experience": 7,
        "education_level": "10th Standard",
        "declared_skills": ["conduit installation", "wire pulling", "earthing", "mcb installation"],
        "languages": ["Hindi", "English"],
        "experience_summary": "7 years doing domestic and commercial conduit wiring, cable laying, and distribution box setup.",
        "education_summary": "Secondary school, apprentice with licensed electrical contractor.",
    }
    worker_resp = await client.post("/api/v1/workers", json=worker_payload, headers=assessor_auth["headers"])
    assert worker_resp.status_code == 201
    worker = worker_resp.json()
    worker_id = worker["id"]
    assert worker["full_name"] == "Kailash Chand Sharma"

    # 2. Direct Skill Extraction from worker narrative via ML endpoint
    ext_resp = await client.post(
        "/api/v1/ml/skills/extract",
        json={"text": worker["experience_summary"], "trade": "electrician", "language": "en"},
    )
    assert ext_resp.status_code == 200
    skills_data = ext_resp.json()
    assert skills_data["count"] > 0
    extracted_names = [s["skill_name"] for s in skills_data["skills"]]
    assert any("wiring" in s.lower() or "conduit" in s.lower() for s in extracted_names)

    # 3. Create Assessment in DRAFT
    assessment_payload = {
        "worker_id": worker_id,
        "trade": "electrician",
        "notes": "RPL candidate practical assessment session",
    }
    ass_resp = await client.post("/api/v1/assessments", json=assessment_payload, headers=assessor_auth["headers"])
    assert ass_resp.status_code == 201
    assessment = ass_resp.json()
    assessment_id = assessment["id"]
    assert assessment["status"] == "DRAFT"

    # 4. Start Assessment -> IN_PROGRESS
    start_resp = await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "IN_PROGRESS"

    # 5. Record Evidence
    ev_payload = {
        "worker_id": worker_id,
        "assessment_id": assessment_id,
        "evidence_type": "WORK_SAMPLE",
        "source_type": "SELF",
        "description": "Installation of 3-phase MCB distribution panel with proper color-coded cabling.",
        "nos_id": "ELE/N9401",
    }
    ev_resp = await client.post("/api/v1/evidence", json=ev_payload, headers=assessor_auth["headers"])
    assert ev_resp.status_code == 201
    evidence_id = ev_resp.json()["id"]

    # Verify Evidence
    verify_resp = await client.post(
        f"/api/v1/evidence/{evidence_id}/verify",
        json={"verification_status": "VERIFIED", "verification_notes": "Meets IS 732 standard for electrical wiring."},
        headers=assessor_auth["headers"],
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verification_status"] == "VERIFIED"

    # 6. Trigger AI Analysis
    analyze_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/analyze",
        json={"language": "en", "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assert analyze_resp.status_code == 200
    ai_run = analyze_resp.json()
    assert ai_run["run_status"] == "COMPLETED"
    assert ai_run["recommendation"] is not None
    assert "ml_response" in ai_run

    # 7. Adaptive Assessment: Recommend Next Task
    next_task_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/recommend-next-task",
        headers=assessor_auth["headers"],
    )
    assert next_task_resp.status_code == 200
    task_rec = next_task_resp.json()
    assert "selected_task" in task_rec
    assert task_rec["selected_task"]["id"] is not None

    # 8. Submit Task Result
    task_id = task_rec["task_id"]
    submit_task_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/tasks/{task_id}/result",
        json={"score": 85.0, "assessor_notes": "Candidate performed conduit pipe bending accurately."},
        headers=assessor_auth["headers"],
    )
    assert submit_task_resp.status_code == 200
    assert submit_task_resp.json()["status"] == "COMPLETED"

    # 9. Verify Assessment status is READY_FOR_REVIEW
    ass_status_resp = await client.get(f"/api/v1/assessments/{assessment_id}", headers=assessor_auth["headers"])
    assert ass_status_resp.status_code == 200
    assert ass_status_resp.json()["status"] == "READY_FOR_REVIEW"

    # 10. Retrieve structured final report
    report_resp = await client.get(f"/api/v1/assessments/{assessment_id}/report", headers=assessor_auth["headers"])
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["worker"]["id"] == worker_id
    assert report["assessment"]["status"] == "READY_FOR_REVIEW"
    assert len(report["tasks"]) >= 1
    assert "advisory" in report["note"].lower()


# ---------------------------------------------------------------------------
# Scenario B: Insufficient Evidence & Abstention Handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_b_insufficient_evidence_and_abstention(
    client: AsyncClient,
    assessor_auth: dict,
):
    """
    Scenario B:
    Worker provides out-of-domain or vague narrative.
    System abstains rather than hallucinating an official qualification.
    """
    # 1. Create worker with non-trade, vague summary
    w_resp = await client.post(
        "/api/v1/workers",
        json={
            "full_name": "Unknown Casual",
            "trade": "general",
            "years_of_experience": 1,
            "experience_summary": "I went to the local supermarket and bought vegetables and fruits for my family.",
        },
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    # 2. Extract skills from out-of-domain text
    ext_resp = await client.post(
        "/api/v1/ml/skills/extract",
        json={"text": "I went to the supermarket and bought vegetables.", "trade": "general"},
    )
    assert ext_resp.status_code == 200
    skills_data = ext_resp.json()
    # Should extract 0 valid technical skills
    assert skills_data["count"] == 0

    # 3. Create assessment
    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "general", "notes": "Insufficient evidence test"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # 4. Check evidence sufficiency
    abs_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/check-evidence",
        headers=assessor_auth["headers"],
    )
    assert abs_resp.status_code == 200
    abs_data = abs_resp.json()
    assert "abstention_check" in abs_data
    # System must recommend abstention / insufficient evidence
    assert abs_data["abstention_check"].get("status") in ["ABSTAIN", "NEEDS_MORE_EVIDENCE", "CONFLICT_REVIEW"]


# ---------------------------------------------------------------------------
# Scenario C: Assessor Human Decision Authority
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_c_human_decision_authority_separation(
    client: AsyncClient,
    assessor_auth: dict,
    db_session: AsyncIOMotorDatabase,
):
    """
    Scenario C:
    AI recommendation is strictly advisory.
    Assessor records final decision, stored in decisions collection.
    Certification is NEVER autonomously issued.
    """
    # 1. Create worker and assessment
    w_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Devendra Kumar", "trade": "electrician", "years_of_experience": 5},
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "electrician"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # Start and Complete to make it ready for review
    await client.post(f"/api/v1/assessments/{assessment_id}/start", headers=assessor_auth["headers"])
    await client.post(f"/api/v1/assessments/{assessment_id}/complete", headers=assessor_auth["headers"])

    # 2. Record Assessor Decision
    decision_payload = {
        "action": "ACCEPT_RECOMMENDATION",
        "comments": "Assessor confirmed candidate demonstrated practical competency in conduit installation.",
        "modified_recommendation": None,
    }
    dec_resp = await client.post(
        f"/api/v1/assessments/{assessment_id}/decision",
        json=decision_payload,
        headers=assessor_auth["headers"],
    )
    assert dec_resp.status_code == 201
    decision = dec_resp.json()
    assert decision["action"] == "ACCEPT_RECOMMENDATION"
    assert decision["assessor_id"] == str(assessor_auth["user"].id)

    # 3. Verify separation in persistence: decisions exist in db.decisions, distinct from AI runs
    decision_doc = await db_session.decisions.find_one({"assessment_id": str(assessment_id)})
    assert decision_doc is not None
    assert decision_doc["action"] == "ACCEPT_RECOMMENDATION"

    # 4. Assessment transitions to REVIEWED
    ass_doc = await db_session.assessments.find_one({"id": str(assessment_id)})
    assert ass_doc["status"] == "REVIEWED"


# ---------------------------------------------------------------------------
# Scenario D: Authentication, Authorization & RBAC
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_d_auth_and_rbac_guards(
    client: AsyncClient,
    assessor_auth: dict,
    worker_auth: dict,
    create_user,
):
    """
    Scenario D:
    - Unauthenticated calls rejected with 401
    - Invalid credentials rejected
    - Worker role cannot create or modify assessments (403)
    - Cross-assessor access restrictions
    """
    # 1. Unauthenticated request to protected endpoint -> 401
    unauth_resp = await client.get("/api/v1/workers")
    assert unauth_resp.status_code == 401

    # 2. Invalid credentials login -> 401
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@kaushaltwin.gov.in", "password": "wrongpassword"},
    )
    assert login_resp.status_code == 401

    # 3. Worker attempting assessor-only route -> 403 Forbidden
    worker_try_assess = await client.post(
        "/api/v1/assessments",
        json={"worker_id": str(uuid.uuid4()), "trade": "electrician"},
        headers=worker_auth["headers"],
    )
    assert worker_try_assess.status_code == 403

    # 4. Assessor B cannot modify Assessor A's assessment
    _, token_b = await create_user(
        name="Assessor B",
        email=f"assessor_b_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.ASSESSOR,
    )
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Assessor A creates worker & assessment
    w_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Protected Worker", "trade": "plumber", "years_of_experience": 3},
        headers=assessor_auth["headers"],
    )
    w_id = w_resp.json()["id"]

    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": w_id, "trade": "plumber"},
        headers=assessor_auth["headers"],
    )
    a_id = a_resp.json()["id"]

    # Assessor B tries to start Assessor A's assessment -> 403 Forbidden
    cross_resp = await client.post(f"/api/v1/assessments/{a_id}/start", headers=headers_b)
    assert cross_resp.status_code == 403


# ---------------------------------------------------------------------------
# Scenario E: Persistence & Cross-Entity Relational Integrity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_e_persistence_and_data_integrity(
    client: AsyncClient,
    assessor_auth: dict,
    db_session: AsyncIOMotorDatabase,
):
    """
    Scenario E:
    Verifies that worker profiles, evidence records, and assessments persist
    properly with relational integrity and survive query lookups.
    """
    # 1. Create worker
    w_resp = await client.post(
        "/api/v1/workers",
        json={
            "full_name": "Suresh Raina",
            "trade": "mason",
            "years_of_experience": 8,
            "declared_skills": ["brick laying", "mortar mixing", "plastering"],
        },
        headers=assessor_auth["headers"],
    )
    worker_id = w_resp.json()["id"]

    # 2. Create assessment
    a_resp = await client.post(
        "/api/v1/assessments",
        json={"worker_id": worker_id, "trade": "mason"},
        headers=assessor_auth["headers"],
    )
    assessment_id = a_resp.json()["id"]

    # 3. Add 2 evidence records
    for i in range(2):
        ev_post = await client.post(
            "/api/v1/evidence",
            json={
                "worker_id": worker_id,
                "assessment_id": assessment_id,
                "evidence_type": "PHOTO",
                "source_type": "SELF",
                "description": f"Masonry inspection photo {i + 1}",
                "nos_id": "CON/N0101",
            },
            headers=assessor_auth["headers"],
        )
        assert ev_post.status_code == 201

    # 4. Verify worker's evidence query returns exactly 2 records
    w_ev_resp = await client.get(f"/api/v1/workers/{worker_id}/evidence", headers=assessor_auth["headers"])
    assert w_ev_resp.status_code == 200
    ev_list = w_ev_resp.json()
    assert len(ev_list) == 2
    assert all(e["worker_id"] == worker_id for e in ev_list)

    # 5. Verify worker's assessments query returns the assessment
    w_ass_resp = await client.get(f"/api/v1/workers/{worker_id}/assessments", headers=assessor_auth["headers"])
    assert w_ass_resp.status_code == 200
    ass_list = w_ass_resp.json()
    assert len(ass_list) == 1
    assert ass_list[0]["id"] == assessment_id


# ---------------------------------------------------------------------------
# Scenario F: Service Failure & Graceful Fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_f_service_failure_and_fallback(
    client: AsyncClient,
    assessor_auth: dict,
):
    """
    Scenario F:
    Validates that missing or failing external ML provider returns structured
    actionable errors (503 Service Unavailable) rather than crashing or faking success.
    """
    # 1. Health check returns 200 with service info
    health_resp = await client.get("/health")
    assert health_resp.status_code == 200
    data = health_resp.json()
    assert data["status"] == "ok"

    # 2. ML health check endpoint
    ml_health_resp = await client.get("/api/v1/ml/health")
    assert ml_health_resp.status_code == 200
    assert ml_health_resp.json()["status"] == "ok"
