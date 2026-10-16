"""
KaushalTwin Backend — API Routes: Audit Ledger

GET /api/v1/audit/events — Retrieve append-only audit log events (assessors/admins only)
GET /api/v1/audit/verify — Independently recompute and verify SHA-256 hash chain integrity
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, require_assessor
from app.db.models.user import User
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditEventItem(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str
    actor_label: str
    actor_role: str = "SYSTEM"
    actor_user_id: Optional[str] = None
    prev_hash: Optional[str] = None
    integrity_hash: Optional[str] = None
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AuditListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    skip: int
    limit: int


class AuditVerificationResponse(BaseModel):
    status: str
    is_valid: bool
    total_events: int
    verified_events: int
    corrupted_events: int
    broken_links: int
    errors: list[dict[str, Any]] = []
    guarantee: str
    explanation: str


@router.get(
    "/events",
    response_model=AuditListResponse,
    summary="List audit events with optional filtering",
)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AuditListResponse:
    """Retrieve chronologically ordered audit events. Assessors and admins only."""
    items, total = await audit_service.list_audit_events(
        db,
        skip=skip,
        limit=limit,
        action=action,
        entity_type=entity_type,
        search=search,
    )
    return AuditListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/verify",
    response_model=AuditVerificationResponse,
    summary="Verify cryptographic SHA-256 hash chain integrity",
)
async def verify_ledger(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AuditVerificationResponse:
    """
    Independently recomputes all SHA-256 hashes and verifies hash chain continuity.
    Detects any payload tampering, record deletions, or event reordering.
    """
    result = await audit_service.verify_audit_log_integrity(db)
    return AuditVerificationResponse(**result)
