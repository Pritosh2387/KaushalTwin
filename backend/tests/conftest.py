"""
KaushalTwin Backend — Test Configuration & Fixtures with MongoDB
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Force testing configuration before app imports
os.environ["APP_ENV"] = "testing"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["MONGODB_DB_NAME"] = "kaushaltwin_test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-1234567890-test-secret"
os.environ["ML_SERVICE_URL"] = "http://localhost:8000"

# Create a temporary directory for uploads
test_upload_dir = tempfile.mkdtemp(prefix="test_uploads_")
os.environ["UPLOAD_DIRECTORY"] = test_upload_dir

from app.core.config import settings
settings.UPLOAD_DIRECTORY = test_upload_dir
settings.MONGODB_URL = "mongodb://localhost:27017"
settings.MONGODB_DB_NAME = "kaushaltwin_test"

from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.db.mongodb import ensure_indexes, mongo_manager
from app.db.models.user import User, UserRole
from app.services.ml_client import init_ml_client, close_ml_client
from app.main import app


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Provide a fresh MongoDB database connection per test function."""
    client = AsyncIOMotorClient("mongodb://localhost:27017", uuidRepresentation="standard")
    db = client["kaushaltwin_test"]
    mongo_manager.client = client
    mongo_manager.db = db

    # Clean existing collections
    collections = await db.list_collection_names()
    for col in collections:
        await db[col].drop()

    await ensure_indexes(db)
    await init_ml_client(app)

    yield db

    # Cleanup after test
    try:
        collections = await db.list_collection_names()
        for col in collections:
            await db[col].drop()
    except Exception:
        pass
    finally:
        client.close()
        shutil.rmtree(test_upload_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def db(db_session: AsyncIOMotorDatabase) -> AsyncIOMotorDatabase:
    """Alias for db_session."""
    return db_session


@pytest_asyncio.fixture
async def client(db_session: AsyncIOMotorDatabase) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient wired to the FastAPI app with test MongoDB override."""
    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_user(db_session: AsyncIOMotorDatabase):
    """Factory fixture to create test users in MongoDB with specified roles."""
    async def _make_user(
        name: str,
        email: str,
        role: UserRole = UserRole.WORKER,
        is_active: bool = True,
        password: str = "SecurePass123!",
    ) -> tuple[User, str]:
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email.lower(),
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
        )
        await db_session.users.insert_one(user.to_mongo())

        token = create_access_token(str(user.id))
        return user, token

    return _make_user


@pytest_asyncio.fixture
async def admin_auth(create_user):
    user, token = await create_user(
        name="Admin User",
        email=f"admin_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.ADMIN,
    )
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def assessor_auth(create_user):
    user, token = await create_user(
        name="Assessor Sharma",
        email=f"assessor_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.ASSESSOR,
    )
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}


@pytest_asyncio.fixture
async def worker_auth(create_user):
    user, token = await create_user(
        name="Ramesh Kumar",
        email=f"worker_{uuid.uuid4().hex[:6]}@example.com",
        role=UserRole.WORKER,
    )
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}
