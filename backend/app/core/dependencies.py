"""
KaushalTwin Backend — FastAPI Dependencies

Provides reusable dependency functions for:
- Async MongoDB database instance
- Current authenticated user extraction
- Role-based authorization guards
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token
from app.db.mongodb import get_database
from app.db.models.user import User, UserRole

# ---------------------------------------------------------------------------
# OAuth2 scheme — token expected in Authorization: Bearer <token>
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncIOMotorDatabase:
    """Yield the async MongoDB database instance."""
    return get_database()


# ---------------------------------------------------------------------------
# Current user extraction
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> User:
    """
    Validate the bearer token, load the User from MongoDB, and
    raise HTTP 401 for any authentication failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise credentials_exception

    queries = [{"id": user_id_str}]
    try:
        queries.append({"id": uuid.UUID(user_id_str)})
    except Exception:
        pass

    user_doc = await db.users.find_one({"$or": queries})
    if user_doc is None:
        raise credentials_exception

    return User.from_mongo(user_doc)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Reject inactive accounts."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return current_user


# ---------------------------------------------------------------------------
# Role guards (return dependency callables)
# ---------------------------------------------------------------------------

def require_role(*roles: UserRole):
    """
    Factory that returns a dependency enforcing the caller has one of the
    listed roles.
    """

    async def _guard(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {[r.value for r in roles]}",
            )
        return current_user

    return _guard


# Convenience shortcuts
require_admin = require_role(UserRole.ADMIN)
require_assessor = require_role(UserRole.ASSESSOR, UserRole.ADMIN)
require_worker = require_role(UserRole.WORKER, UserRole.ASSESSOR, UserRole.ADMIN)
