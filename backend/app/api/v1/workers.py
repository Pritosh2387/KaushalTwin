"""
KaushalTwin Backend — API Routes: Workers

POST   /api/v1/workers                          — Create worker profile
GET    /api/v1/workers                          — List workers (assessors/admins)
GET    /api/v1/workers/{worker_id}              — Get worker profile
PATCH  /api/v1/workers/{worker_id}             — Update worker profile
GET    /api/v1/workers/{worker_id}/assessments  — List worker's assessments
GET    /api/v1/workers/{worker_id}/evidence     — List worker's evidence records
"""

from __future__ import annotations

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_active_user, require_assessor
from app.db.models.user import User, UserRole
from app.db.models.worker import WorkerProfile
from app.db.models.assessment import Assessment
from app.db.models.evidence import EvidenceRecord
from app.schemas.worker import (
    WorkerCreateRequest,
    WorkerUpdateRequest,
    WorkerResponse,
    WorkerListResponse,
)
from app.schemas.assessment import AssessmentResponse
from app.schemas.evidence import EvidenceResponse
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workers", tags=["Workers"])


def _assert_worker_access(worker: WorkerProfile, current_user: User) -> None:
    """Raise 403 if the current user is not authorized to access this worker's data."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.ASSESSOR:
        return
    # Worker role: only own profile
    if worker.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )


@router.post(
    "",
    response_model=WorkerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new worker profile",
)
async def create_worker(
    body: WorkerCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerResponse:
    """
    Create a worker profile. Assessors and admins only.
    The worker does not need a user account — walk-in candidates are supported.
    """
    worker = WorkerProfile(
        id=uuid.uuid4(),
        full_name=body.full_name,
        trade=body.trade,
        years_of_experience=body.years_of_experience,
        experience_summary=body.experience_summary,
        education_summary=body.education_summary,
        user_id=body.user_id,
        registered_by_id=current_user.id,
    )
    db.add(worker)
    await db.flush()

    await audit_service.record_event(
        db,
        action="WORKER_CREATED",
        entity_type="WorkerProfile",
        entity_id=str(worker.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"trade": worker.trade},
    )

    logger.info("Worker profile created: %s by %s", worker.id, current_user.email)
    return WorkerResponse.model_validate(worker)


@router.get(
    "",
    response_model=WorkerListResponse,
    summary="List worker profiles (assessors and admins)",
)
async def list_workers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    trade: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerListResponse:
    """Paginated list of worker profiles. Assessors and admins only."""
    query = select(WorkerProfile)
    if trade:
        query = query.where(WorkerProfile.trade == trade)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.offset(skip).limit(limit))
    workers = result.scalars().all()

    return WorkerListResponse(
        items=[WorkerResponse.model_validate(w) for w in workers],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
    summary="Get a worker profile by ID",
)
async def get_worker(
    worker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == worker_id)
    )
    worker: WorkerProfile | None = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    _assert_worker_access(worker, current_user)
    return WorkerResponse.model_validate(worker)


@router.patch(
    "/{worker_id}",
    response_model=WorkerResponse,
    summary="Update a worker profile",
)
async def update_worker(
    worker_id: uuid.UUID,
    body: WorkerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerResponse:
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == worker_id)
    )
    worker: WorkerProfile | None = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(worker, field, value)

    await audit_service.record_event(
        db,
        action="WORKER_UPDATED",
        entity_type="WorkerProfile",
        entity_id=str(worker.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"updated_fields": list(update_data.keys())},
    )

    return WorkerResponse.model_validate(worker)


@router.get(
    "/{worker_id}/assessments",
    response_model=list[AssessmentResponse],
    summary="List assessments for a worker",
)
async def get_worker_assessments(
    worker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AssessmentResponse]:
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    _assert_worker_access(worker, current_user)

    result2 = await db.execute(
        select(Assessment).where(Assessment.worker_id == worker_id)
    )
    assessments = result2.scalars().all()
    return [AssessmentResponse.model_validate(a) for a in assessments]


@router.get(
    "/{worker_id}/evidence",
    response_model=list[EvidenceResponse],
    summary="List evidence records for a worker",
)
async def get_worker_evidence(
    worker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EvidenceResponse]:
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    _assert_worker_access(worker, current_user)

    result2 = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.worker_id == worker_id)
    )
    records = result2.scalars().all()
    return [EvidenceResponse.model_validate(r) for r in records]
