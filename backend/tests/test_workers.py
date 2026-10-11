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
