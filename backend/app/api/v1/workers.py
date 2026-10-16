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
    WorkerNarrativeRequest,
    WorkerNarrativeAnalyzeRequest,
    WorkerNarrativeAnalyzeResponse,
)
from app.schemas.assessment import AssessmentResponse
from app.schemas.evidence import EvidenceResponse
from app.db.models.assessment import Assessment
from app.db.models.mongo_models import EvidenceRecord
from app.services import audit_service
from ml.services.skill_service import extract_skills, map_skills_to_nos

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


def _match_id(val: uuid.UUID | str) -> dict:
    s_val = str(val)
    try:
        u_val = uuid.UUID(s_val)
        return {"$in": [s_val, u_val]}
    except (ValueError, TypeError):
        return {"$eq": s_val}


async def _resolve_current_worker(db: AsyncIOMotorDatabase, current_user: User) -> WorkerProfile:
    """Resolve the WorkerProfile document for the authenticated user, or auto-initialize one."""
    user_q = _match_id(current_user.id)
    doc = await db.workers.find_one({"user_id": user_q})
    if not doc and current_user.email:
        doc = await db.workers.find_one({"email": current_user.email})
    if not doc and current_user.name:
        doc = await db.workers.find_one({"full_name": current_user.name})
        if not doc:
            doc = await db.workers.find_one({"full_name": {"$regex": f"^{current_user.name}", "$options": "i"}})
    if doc and not doc.get("user_id"):
        await db.workers.update_one({"_id": doc["_id"]}, {"$set": {"user_id": str(current_user.id)}})
        doc["user_id"] = str(current_user.id)

    if not doc:
        new_worker = WorkerProfile(
            id=uuid.uuid4(),
            user_id=current_user.id,
            full_name=current_user.name,
            email=current_user.email,
            trade="General",
            years_of_experience=0,
            assessment_status="NOT_STARTED",
        )
        await db.workers.insert_one(new_worker.to_mongo())
        doc = new_worker.to_mongo()

    return WorkerProfile.from_mongo(doc)


@router.get(
    "/me",
    response_model=WorkerResponse,
    summary="Get current authenticated worker's profile",
)
async def get_my_worker_profile(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    if current_user.role != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with WORKER role have a worker profile",
        )
    worker = await _resolve_current_worker(db, current_user)
    return WorkerResponse.model_validate(worker)


@router.patch(
    "/me",
    response_model=WorkerResponse,
    summary="Update current authenticated worker's profile",
)
async def update_my_worker_profile(
    body: WorkerUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    if current_user.role != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with WORKER role have a worker profile",
        )
    worker = await _resolve_current_worker(db, current_user)
    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    if "work_narrative" in update_data and "informal_work_description" not in update_data:
        update_data["informal_work_description"] = update_data["work_narrative"]
    elif "informal_work_description" in update_data and "work_narrative" not in update_data:
        update_data["work_narrative"] = update_data["informal_work_description"]

    target_id_q = _match_id(worker.id)
    await db.workers.update_one({"id": target_id_q}, {"$set": update_data})
    updated_doc = await db.workers.find_one({"id": target_id_q})
    updated_worker = WorkerProfile.from_mongo(updated_doc)

    await audit_service.record_event(
        db,
        action="WORKER_UPDATED",
        entity_type="WorkerProfile",
        entity_id=str(worker.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"updated_fields": list(update_data.keys())},
    )
    return WorkerResponse.model_validate(updated_worker)


@router.patch(
    "/me/narrative",
    response_model=WorkerResponse,
    summary="Save work experience narrative for current authenticated worker",
)
async def save_my_work_narrative(
    body: WorkerNarrativeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    if current_user.role != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with WORKER role have a work narrative",
        )
    worker = await _resolve_current_worker(db, current_user)
    now = datetime.now(timezone.utc)
    target_id_q = _match_id(worker.id)
    await db.workers.update_one(
        {"id": target_id_q},
        {
            "$set": {
                "work_narrative": body.narrative,
                "informal_work_description": body.narrative,
                "updated_at": now,
            }
        },
    )
    updated_doc = await db.workers.find_one({"id": target_id_q})
    updated_worker = WorkerProfile.from_mongo(updated_doc)

    await audit_service.record_event(
        db,
        action="WORKER_NARRATIVE_UPDATED",
        entity_type="WorkerProfile",
        entity_id=str(worker.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"narrative_length": len(body.narrative)},
    )
    return WorkerResponse.model_validate(updated_worker)


@router.post(
    "/me/analyze-narrative",
    response_model=WorkerNarrativeAnalyzeResponse,
    summary="Extract skills and map candidate NOS standards from worker's narrative",
)
async def analyze_my_work_narrative(
    body: WorkerNarrativeAnalyzeRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WorkerNarrativeAnalyzeResponse:
    if current_user.role != UserRole.WORKER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with WORKER role can analyze work narratives",
        )
    worker = await _resolve_current_worker(db, current_user)
    text_to_analyze = body.narrative or worker.work_narrative or worker.informal_work_description
    if not text_to_analyze or not text_to_analyze.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide or save a work narrative before analyzing skills.",
        )

    # Normalize trade context for ML engine
    raw_trade = (worker.trade or "electrician").lower()
    if "electric" in raw_trade:
        trade_context = "electrician"
    elif "weld" in raw_trade:
        trade_context = "welder"
    elif "plumb" in raw_trade:
        trade_context = "plumber"
    elif "mason" in raw_trade:
        trade_context = "mason"
    else:
        trade_context = "general"

    lang = body.language if body.language in ("en", "hi") else "en"

    # 1. Skill Extraction
    extracted_skills_list: list[dict] = []
    try:
        extraction_res = extract_skills(
            text=text_to_analyze,
            language=lang,
            trade=trade_context,
        )
        extracted_skills_list = [s.model_dump() for s in extraction_res.skills]
    except Exception as exc:
        logger.warning("Error in worker narrative skill extraction: %s", exc)

    # 2. NOS Candidate Mapping
    nos_mappings_list: list[dict] = []
    if extracted_skills_list:
        try:
            nos_res = map_skills_to_nos(
                skills=extracted_skills_list,
                top_k=3,
            )
            nos_mappings_list = nos_res
        except Exception as exc:
            logger.warning("Error in worker narrative NOS mapping: %s", exc)

    return WorkerNarrativeAnalyzeResponse(
        worker_id=worker.id,
        trade=worker.trade,
        language=lang,
        narrative=text_to_analyze,
        extracted_skills=extracted_skills_list,
        nos_mappings=nos_mappings_list,
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
    id_q = _match_id(worker_id)
    doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
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
    current_user: User = Depends(get_current_active_user),
) -> WorkerResponse:
    id_q = _match_id(worker_id)
    doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    if "work_narrative" in update_data and "informal_work_description" not in update_data:
        update_data["informal_work_description"] = update_data["work_narrative"]
    elif "informal_work_description" in update_data and "work_narrative" not in update_data:
        update_data["work_narrative"] = update_data["informal_work_description"]

    target_id_q = _match_id(worker.id)
    await db.workers.update_one({"id": target_id_q}, {"$set": update_data})
    updated_doc = await db.workers.find_one({"id": target_id_q})
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
    id_q = _match_id(worker_id)
    doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    w_q = _match_id(worker.id)
    cursor = db.assessments.find({"worker_id": w_q})
    items = []
    async for a_doc in cursor:
        items.append(AssessmentResponse.model_validate(Assessment.from_mongo(a_doc)))
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
    id_q = _match_id(worker_id)
    doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    w_q = _match_id(worker.id)
    or_clauses = [{"worker_id": w_q}]
    if worker.user_id:
        or_clauses.append({"worker_id": _match_id(worker.user_id)})
        or_clauses.append({"uploaded_by_id": _match_id(worker.user_id)})
    if current_user.role == UserRole.WORKER:
        or_clauses.append({"uploaded_by_id": _match_id(current_user.id)})

    cursor = db.evidence.find({"$or": or_clauses}).sort("created_at", -1)
    items = []
    async for e_doc in cursor:
        items.append(EvidenceResponse.model_validate(EvidenceRecord.from_mongo(e_doc)))
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
    id_q = _match_id(worker_id)
    doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(doc)
    _assert_worker_access(worker, current_user)

    w_q = _match_id(worker.id)
    # Find the latest successful AI run for this worker
    latest_run = await db.ai_runs.find_one(
        {"worker_id": w_q, "status": {"$in": ["SUCCESS", "COMPLETED"]}},
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

    # Fallback to candidate_competencies from assessments if no AI run yet
    if not competencies:
        assessment_doc = await db.assessments.find_one(
            {"worker_id": w_q, "candidate_competencies": {"$exists": True, "$ne": []}},
            sort=[("created_at", -1)],
        )
        if assessment_doc and assessment_doc.get("candidate_competencies"):
            competencies = assessment_doc["candidate_competencies"]
            has_profile = True

    # Enrich competencies with verified evidence counts and status
    evidence_cursor = db.evidence.find({"worker_id": w_q})
    worker_evs = await evidence_cursor.to_list(length=100)

    enriched_competencies = []
    for comp in competencies:
        c_dict = dict(comp)
        nos_code = c_dict.get("nos_id") or c_dict.get("code")
        matching_evs = [e for e in worker_evs if e.get("nos_id") == nos_code] if nos_code else []
        verified_evs = [e for e in matching_evs if e.get("verification_status") == "VERIFIED"]

        c_dict["evidence_count"] = len(matching_evs)
        c_dict["verified_evidence_count"] = len(verified_evs)
        has_verified_evidence = len(verified_evs) > 0
        c_dict["verified"] = has_verified_evidence
        c_dict["status"] = "Assessor-verified" if has_verified_evidence else "AI-aligned (Advisory)"
        enriched_competencies.append(c_dict)

    status_str = (
        worker.assessment_status.value
        if hasattr(worker.assessment_status, "value")
        else str(worker.assessment_status)
    )

    return WorkerCompetencyProfileResponse(
        worker_id=worker.id,
        trade=worker.trade,
        assessment_status=status_str,
        latest_ai_run_id=uuid.UUID(str(latest_run["id"])) if latest_run and "id" in latest_run else None,
        competencies=enriched_competencies,
        summary=summary,
        skills_extracted=skills_extracted,
        nos_candidates=nos_candidates,
        has_profile=has_profile,
    )

