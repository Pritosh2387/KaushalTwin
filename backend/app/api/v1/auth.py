"""
KaushalTwin Backend — API Routes: Authentication

POST /api/v1/auth/register  — Create new user account (open for demo; restrict in production)
POST /api/v1/auth/login     — Authenticate and get JWT
GET  /api/v1/auth/me        — Get current authenticated user
"""

from __future__ import annotations

import uuid
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account.

    Note: In production, restrict this endpoint to ADMIN-only access or
    replace with an invite-based flow.
    """
    # Validate role
    try:
        role = UserRole(body.role.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {body.role}. Must be WORKER, ASSESSOR, or ADMIN.",
        )

    # Check for existing email
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if result.scalar_one_or_none():
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
    db.add(user)
    await db.flush()  # get the ID without committing

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
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email + password and receive a JWT bearer token."""
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user: User | None = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(str(user.id))
    logger.info("User logged in: %s", user.email)

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
