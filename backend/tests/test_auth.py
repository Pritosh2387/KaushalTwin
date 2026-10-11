"""
Unit and Integration Tests: Authentication & Authorization APIs
"""

import uuid
import pytest
from httpx import AsyncClient

from app.db.models.user import UserRole


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    email = f"worker_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "name": "Suresh Patel",
        "email": email,
        "password": "Password123!",
        "role": "WORKER",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email.lower()
    assert data["role"] == "WORKER"
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, create_user):
    user, _ = await create_user("Existing User", "existing@example.com")
    payload = {
        "name": "Duplicate User",
        "email": "existing@example.com",
        "password": "Password123!",
        "role": "WORKER",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert "Email already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_role(client: AsyncClient):
    payload = {
        "name": "Bad Role User",
        "email": f"bad_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Password123!",
        "role": "SUPERUSER",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, create_user):
    email = f"login_{uuid.uuid4().hex[:6]}@example.com"
    await create_user("Test User", email, password="MySecretPassword123!")

    payload = {"email": email, "password": "MySecretPassword123!"}
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, create_user):
    email = f"wrong_{uuid.uuid4().hex[:6]}@example.com"
    await create_user("Test User", email, password="CorrectPassword123!")

    payload = {"email": email, "password": "WrongPassword123!"}
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    payload = {"email": "nonexistent@example.com", "password": "Password123!"}
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, create_user):
    email = f"inactive_{uuid.uuid4().hex[:6]}@example.com"
    await create_user("Inactive User", email, is_active=False, password="Password123!")

    payload = {"email": email, "password": "Password123!"}
    resp = await client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 403
    assert "inactive" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_me_endpoint_authenticated(client: AsyncClient, worker_auth):
    resp = await client.get("/api/v1/auth/me", headers=worker_auth["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == worker_auth["user"].email
    assert data["role"] == "WORKER"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_me_endpoint_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert resp.status_code == 401
