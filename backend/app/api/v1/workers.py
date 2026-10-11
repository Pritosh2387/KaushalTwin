"""
KaushalTwin Backend — API Routes: Workers

POST   /api/v1/workers                          — Create worker profile
GET    /api/v1/workers                          — List workers (assessors/admins)
GET    /api/v1/workers/{worker_id}              — Get worker profile
PATCH  /api/v1/workers/{worker_id}             — Update worker profile
GET    /api/v1/workers/{worker_id}/assessments  — List worker's assessments
GET    /api/v1/workers/{worker_id}/evidence     — List worker's evidence records
GET    /api/v1/workers/{worker_id}/competency-profile — Aggregated competency profile
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_active_user, require_assessor
from app.db.models.user import User, UserRole
from app.db.models.worker import WorkerProfile
from app.schemas.worker import (
    WorkerCreateRequest,
    WorkerUpdateRequest,
    WorkerResponse,
    WorkerListResponse,
    WorkerCompetencyProfileResponse,
)
from app.schemas.assessment import AssessmentResponse
from app.schemas.evidence import EvidenceResponse
from app.services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workers", tags=["Workers"])


def _assert_worker_access(worker: WorkerProfile, current_user: User) -> None:
    """Raise 403 if the current user is not authorized to access this worker's data."""
    if current_user.role in (UserRole.ADMIN, UserRole.ASSESSOR):
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
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerResponse:
    """
    Create a worker profile in MongoDB. Assessors and admins only.
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
    doc = worker.to_mongo()
    await db.workers.insert_one(doc)

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
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerListResponse:
    """Paginated list of worker profiles. Assessors and admins only."""
    query: dict = {}
    if trade:
        query["trade"] = trade

    total = await db.workers.count_documents(query)
    cursor = db.workers.find(query).skip(skip).limit(limit)
    workers = []
    async for doc in cursor:
        workers.append(WorkerProfile.from_mongo(doc))

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
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    doc = await db.workers.find_one({"id": str(worker_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
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
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> WorkerResponse:
    doc = await db.workers.find_one({"id": str(worker_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)

    await db.workers.update_one({"id": str(worker_id)}, {"$set": update_data})
    updated_doc = await db.workers.find_one({"id": str(worker_id)})
    updated_worker = WorkerProfile.from_mongo(updated_doc)

    await audit_service.record_event(
        db,
        action="WORKER_UPDATED",
        entity_type="WorkerProfile",
        entity_id=str(worker.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"updated_fields": list(body.model_dump(exclude_unset=True).keys())},
    )

    return WorkerResponse.model_validate(updated_worker)


@router.get(
    "/{worker_id}/assessments",
    response_model=list[AssessmentResponse],
    summary="List assessments for a worker",
)
async def get_worker_assessments(
    worker_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AssessmentResponse]:
    doc = await db.workers.find_one({"id": str(worker_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    cursor = db.assessments.find({"worker_id": str(worker_id)})
    items = []
    async for a_doc in cursor:
        items.append(AssessmentResponse.model_validate(a_doc))
    return items


@router.get(
    "/{worker_id}/evidence",
    response_model=list[EvidenceResponse],
    summary="List evidence records for a worker",
)
async def get_worker_evidence(
    worker_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[EvidenceResponse]:
    doc = await db.workers.find_one({"id": str(worker_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    cursor = db.evidence.find({"worker_id": str(worker_id)})
    items = []
    async for e_doc in cursor:
        items.append(EvidenceResponse.model_validate(e_doc))
    return items


@router.get(
    "/{worker_id}/competency-profile",
    response_model=WorkerCompetencyProfileResponse,
    summary="Get aggregated competency profile for a worker",
)
async def get_worker_competency_profile(
    worker_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerCompetencyProfileResponse:
    doc = await db.workers.find_one({"id": str(worker_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    # Find the latest successful AI run for this worker
    latest_run = await db.ai_runs.find_one(
        {"worker_id": str(worker_id), "status": {"$in": ["SUCCESS", "COMPLETED"]}},
        sort=[("created_at", -1)],
    )

    competencies = []
    summary = None
    skills_extracted = []
    nos_candidates = []
    has_profile = False

    if latest_run and latest_run.get("result_payload"):
        ml_data = latest_run["result_payload"]
        twin = ml_data.get("competency_twin", {})
        competencies = twin.get("competencies", [])
        summary = twin.get("summary")
        skills_extracted = ml_data.get("skills", [])
        nos_candidates = ml_data.get("nos_candidates", [])
        has_profile = bool(competencies)

    status_str = (
        worker.assessment_status.value
        if hasattr(worker.assessment_status, "value")
        else str(worker.assessment_status)
    )

    return WorkerCompetencyProfileResponse(
        worker_id=worker.id,
        trade=worker.trade,
        assessment_status=status_str,
        latest_ai_run_id=uuid.UUID(latest_run["id"]) if latest_run and "id" in latest_run else None,
        competencies=competencies,
        summary=summary,
        skills_extracted=skills_extracted,
        nos_candidates=nos_candidates,
        has_profile=has_profile,
    )
