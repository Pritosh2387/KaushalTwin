"""
KaushalTwin Backend — API Routes: Authentication

POST /api/v1/auth/register  — Create new user account (open for demo; restrict in production)
POST /api/v1/auth/login     — Authenticate and get JWT
GET  /api/v1/auth/me        — Get current authenticated user
"""

from __future__ import annotations

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.dependencies import get_db, get_current_active_user
from app.core.security import hash_password, verify_password, create_access_token
from app.db.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: RegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account in MongoDB.
    """
    try:
        role = UserRole(body.role.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {body.role}. Must be WORKER, ASSESSOR, or ADMIN.",
        )

    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        name=body.name,
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        role=role,
        is_active=True,
    )
    user_doc = user.to_mongo()
    await db.users.insert_one(user_doc)

    await audit_service.record_event(
        db,
        action="USER_REGISTERED",
        entity_type="User",
        entity_id=str(user.id),
        actor_user_id=user.id,
        actor_label=user.email,
        metadata={"role": role.value},
    )

    logger.info("New user registered: %s (%s)", user.email, role)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT access token",
)
async def login(
    body: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email + password and receive a JWT bearer token."""
    user_doc = await db.users.find_one({"email": body.email.lower()})

    if not user_doc or not verify_password(body.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(str(user_doc["id"]))
    logger.info("User logged in: %s", user_doc["email"])

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
async def me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the authenticated user's profile. Passwords are never included."""
    return UserResponse.model_validate(current_user)
