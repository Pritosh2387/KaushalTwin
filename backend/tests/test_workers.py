"""
Unit and Integration Tests: Worker Management APIs
"""

import uuid
import pytest
from httpx import AsyncClient

from app.db.models.user import UserRole
from app.db.models.worker import WorkerProfile


@pytest.mark.asyncio
async def test_create_worker_assessor_success(client: AsyncClient, assessor_auth):
    payload = {
        "full_name": "Rajesh Sharma",
        "trade": "electrician",
        "years_of_experience": 5,
        "experience_summary": "5 years doing house wiring and DB installation.",
        "education_summary": "10th pass, ITI apprenticeship",
    }
    resp = await client.post("/api/v1/workers", json=payload, headers=assessor_auth["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Rajesh Sharma"
    assert data["trade"] == "electrician"
    assert data["years_of_experience"] == 5
    assert data["assessment_status"] == "NOT_STARTED"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_worker_forbidden_for_worker(client: AsyncClient, worker_auth):
    payload = {
        "full_name": "Unauthorized Worker",
        "trade": "plumber",
        "years_of_experience": 2,
    }
    resp = await client.post("/api/v1/workers", json=payload, headers=worker_auth["headers"])
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_workers_pagination(client: AsyncClient, assessor_auth):
    # Create two workers
    for i in range(2):
        await client.post(
            "/api/v1/workers",
            json={
                "full_name": f"Worker {uuid.uuid4().hex[:4]}",
                "trade": "electrician",
                "years_of_experience": i + 1,
            },
            headers=assessor_auth["headers"],
        )

    resp = await client.get("/api/v1/workers?skip=0&limit=10", headers=assessor_auth["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_get_worker_by_id(client: AsyncClient, assessor_auth):
    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Karan Singh", "trade": "carpenter", "years_of_experience": 3},
        headers=assessor_auth["headers"],
    )
    worker_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/workers/{worker_id}", headers=assessor_auth["headers"])
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == worker_id


@pytest.mark.asyncio
async def test_get_worker_not_found(client: AsyncClient, assessor_auth):
    random_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/workers/{random_id}", headers=assessor_auth["headers"])
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_worker_cross_user_access_prevention(client: AsyncClient, create_user):
    # Worker 1
    w1_user, w1_token = await create_user("Worker One", "w1@example.com", role=UserRole.WORKER)
    # Worker 2
    w2_user, w2_token = await create_user("Worker Two", "w2@example.com", role=UserRole.WORKER)
    # Assessor creates profile linked to Worker 1
    assessor, a_token = await create_user("Assessor", "assessor_x@example.com", role=UserRole.ASSESSOR)

    create_resp = await client.post(
        "/api/v1/workers",
        json={
            "full_name": "Worker One",
            "trade": "electrician",
            "years_of_experience": 4,
            "user_id": str(w1_user.id),
        },
        headers={"Authorization": f"Bearer {a_token}"},
    )
    w1_profile_id = create_resp.json()["id"]

    # Worker 1 can view own profile
    w1_resp = await client.get(
        f"/api/v1/workers/{w1_profile_id}",
        headers={"Authorization": f"Bearer {w1_token}"},
    )
    assert w1_resp.status_code == 200

    # Worker 2 attempts to view Worker 1's profile -> 403 Forbidden
    w2_resp = await client.get(
        f"/api/v1/workers/{w1_profile_id}",
        headers={"Authorization": f"Bearer {w2_token}"},
    )
    assert w2_resp.status_code == 403


@pytest.mark.asyncio
async def test_update_worker(client: AsyncClient, assessor_auth):
    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Old Name", "trade": "welder", "years_of_experience": 2},
        headers=assessor_auth["headers"],
    )
    worker_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/workers/{worker_id}",
        json={"full_name": "Updated Name", "years_of_experience": 4},
        headers=assessor_auth["headers"],
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["full_name"] == "Updated Name"
    assert patch_resp.json()["years_of_experience"] == 4


@pytest.mark.asyncio
async def test_worker_competency_profile_empty(client: AsyncClient, assessor_auth):
    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Profile Test", "trade": "electrician", "years_of_experience": 1},
        headers=assessor_auth["headers"],
    )
    worker_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/workers/{worker_id}/competency-profile",
        headers=assessor_auth["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["worker_id"] == worker_id
    assert data["has_profile"] is False
    assert data["competencies"] == []


@pytest.mark.asyncio
async def test_worker_get_own_profile_via_me(client: AsyncClient, create_user):
    w_user, w_token = await create_user("Ramesh Worker", "ramesh_me@example.com", role=UserRole.WORKER)
    # Assessor links worker profile
    assessor, a_token = await create_user("Assessor", "assessor_me@example.com", role=UserRole.ASSESSOR)
    await client.post(
        "/api/v1/workers",
        json={"full_name": "Ramesh Worker", "trade": "electrician", "years_of_experience": 5, "user_id": str(w_user.id)},
        headers={"Authorization": f"Bearer {a_token}"},
    )

    me_resp = await client.get("/api/v1/workers/me", headers={"Authorization": f"Bearer {w_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Ramesh Worker"
    assert me_resp.json()["trade"] == "electrician"


@pytest.mark.asyncio
async def test_worker_can_update_own_profile(client: AsyncClient, create_user):
    w_user, w_token = await create_user("Self Updating Worker", "self_up@example.com", role=UserRole.WORKER)
    assessor, a_token = await create_user("Assessor", "assessor_up@example.com", role=UserRole.ASSESSOR)
    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Self Updating Worker", "trade": "plumber", "years_of_experience": 2, "user_id": str(w_user.id)},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    profile_id = create_resp.json()["id"]

    # Worker updates their own experience and phone
    patch_resp = await client.patch(
        f"/api/v1/workers/{profile_id}",
        json={"years_of_experience": 4, "phone": "+91 99999 88888", "declared_skills": ["Pipe Fitting", "Leak Testing"]},
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["years_of_experience"] == 4
    assert data["phone"] == "+91 99999 88888"
    assert "Pipe Fitting" in data["declared_skills"]


@pytest.mark.asyncio
async def test_worker_cannot_update_other_worker_profile(client: AsyncClient, create_user):
    w1_user, w1_token = await create_user("Worker One", "w1_cross@example.com", role=UserRole.WORKER)
    w2_user, w2_token = await create_user("Worker Two", "w2_cross@example.com", role=UserRole.WORKER)
    assessor, a_token = await create_user("Assessor", "assessor_cross@example.com", role=UserRole.ASSESSOR)

    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Worker One", "trade": "carpenter", "years_of_experience": 3, "user_id": str(w1_user.id)},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    w1_profile_id = create_resp.json()["id"]

    # Worker 2 attempts to PATCH Worker 1's profile -> 403 Forbidden
    patch_resp = await client.patch(
        f"/api/v1/workers/{w1_profile_id}",
        json={"full_name": "Hacked Name"},
        headers={"Authorization": f"Bearer {w2_token}"},
    )
    assert patch_resp.status_code == 403


@pytest.mark.asyncio
async def test_worker_can_get_own_evidence(client: AsyncClient, create_user):
    w_user, w_token = await create_user("Evidence Worker", "w_ev@example.com", role=UserRole.WORKER)
    assessor, a_token = await create_user("Assessor Ev", "assessor_ev@example.com", role=UserRole.ASSESSOR)

    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Evidence Worker", "trade": "mason", "years_of_experience": 4, "user_id": str(w_user.id)},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    profile_id = create_resp.json()["id"]

    # Submit evidence for this worker
    ev_resp = await client.post(
        "/api/v1/evidence",
        json={
            "worker_id": profile_id,
            "evidence_type": "WORK_SAMPLE",
            "source_type": "SELF",
            "description": "Masonry boundary wall photograph.",
        },
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert ev_resp.status_code == 201

    # Worker fetches their own evidence
    get_ev_resp = await client.get(
        f"/api/v1/workers/{profile_id}/evidence",
        headers={"Authorization": f"Bearer {w_token}"},
    )
    assert get_ev_resp.status_code == 200
    items = get_ev_resp.json()
    assert len(items) >= 1
    assert items[0]["description"] == "Masonry boundary wall photograph."


@pytest.mark.asyncio
async def test_worker_cannot_get_other_worker_evidence(client: AsyncClient, create_user):
    w1_user, w1_token = await create_user("Worker A", "wa_ev@example.com", role=UserRole.WORKER)
    w2_user, w2_token = await create_user("Worker B", "wb_ev@example.com", role=UserRole.WORKER)
    assessor, a_token = await create_user("Assessor Ev2", "assessor_ev2@example.com", role=UserRole.ASSESSOR)

    create_resp = await client.post(
        "/api/v1/workers",
        json={"full_name": "Worker A", "trade": "mason", "years_of_experience": 4, "user_id": str(w1_user.id)},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    w1_profile_id = create_resp.json()["id"]

    # Worker 2 attempts to fetch Worker 1's evidence -> 403 Forbidden
    get_resp = await client.get(
        f"/api/v1/workers/{w1_profile_id}/evidence",
        headers={"Authorization": f"Bearer {w2_token}"},
    )
    assert get_resp.status_code == 403


