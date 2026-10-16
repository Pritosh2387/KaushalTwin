"""
KaushalTwin Backend — API Routes: Evidence

POST   /api/v1/evidence                           — Submit evidence metadata
POST   /api/v1/evidence/upload/{worker_id}        — Upload evidence file
GET    /api/v1/evidence                           — List evidence records
GET    /api/v1/evidence/{evidence_id}             — Get evidence record
PATCH  /api/v1/evidence/{evidence_id}             — Update evidence metadata
POST   /api/v1/evidence/{evidence_id}/verify      — Verify or reject evidence (assessors)
GET    /api/v1/evidence/{evidence_id}/download    — Download evidence file
"""

from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_active_user, require_assessor
from app.db.models.user import User, UserRole
from app.db.models.worker import WorkerProfile
from app.db.models.evidence import (
    EvidenceRecord,
    EvidenceType,
    EvidenceSourceType,
    EvidenceVerificationStatus,
)
from app.schemas.evidence import (
    EvidenceCreateRequest,
    EvidenceUpdateRequest,
    EvidenceVerifyRequest,
    EvidenceResponse,
    EvidenceListResponse,
)
from app.services import audit_service, storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evidence", tags=["Evidence"])


def _match_id(val: uuid.UUID | str) -> dict:
    s_val = str(val)
    try:
        u_val = uuid.UUID(s_val)
        return {"$in": [s_val, u_val]}
    except (ValueError, TypeError):
        return {"$eq": s_val}


def _assert_evidence_access(record: EvidenceRecord, current_user: User, worker_user_id: Optional[uuid.UUID | str] = None) -> None:
    if current_user.role in (UserRole.ADMIN, UserRole.ASSESSOR):
        return
    if str(record.uploaded_by_id) == str(current_user.id):
        return
    if worker_user_id and str(worker_user_id) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.get(
    "",
    response_model=EvidenceListResponse,
    summary="List all evidence records with optional filtering",
)
async def list_evidence(
    skip: int = 0,
    limit: int = 50,
    verification_status: Optional[str] = None,
    worker_id: Optional[uuid.UUID] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceListResponse:
    query = {}
    if current_user.role == UserRole.WORKER:
        user_match = [str(current_user.id), current_user.id]
        worker_doc = await db.workers.find_one({"user_id": {"$in": user_match}})
        if worker_doc:
            w_id = worker_doc["id"]
            w_match = [str(w_id), w_id]
            query["$or"] = [
                {"uploaded_by_id": {"$in": user_match}},
                {"worker_id": {"$in": w_match}},
            ]
        else:
            query["uploaded_by_id"] = {"$in": user_match}
    elif worker_id:
        query["worker_id"] = _match_id(worker_id)

    if verification_status:
        v_upper = verification_status.upper().strip()
        if v_upper in ("PENDING", "PENDING_REVIEW"):
            query["verification_status"] = {"$in": ["PENDING", "PENDING_REVIEW"]}
        else:
            query["verification_status"] = v_upper

    total = await db.evidence.count_documents(query)
    cursor = db.evidence.find(query).skip(skip).limit(limit).sort("created_at", -1)
    docs = await cursor.to_list(length=limit)
    items = [EvidenceResponse.model_validate(EvidenceRecord.from_mongo(d)) for d in docs]
    return EvidenceListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit evidence metadata (without file)",
)
async def create_evidence(
    body: EvidenceCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    id_q = _match_id(body.worker_id)
    worker_doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not worker_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(worker_doc)
    if current_user.role == UserRole.WORKER and str(worker.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        ev_type = EvidenceType(body.evidence_type)
        src_type = EvidenceSourceType(body.source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    now = datetime.now(timezone.utc)
    record = EvidenceRecord(
        id=uuid.uuid4(),
        worker_id=worker.id,
        assessment_id=body.assessment_id,
        uploaded_by_id=current_user.id,
        evidence_type=ev_type.value,
        source_type=src_type.value,
        description=body.description,
        nos_id=body.nos_id,
        verification_status=EvidenceVerificationStatus.UNVERIFIED.value,
        metadata_json=json.dumps(body.metadata_json) if body.metadata_json else None,
        created_at=now,
        updated_at=now,
    )
    doc = record.to_mongo()
    await db.evidence.insert_one(doc)

    await audit_service.record_event(
        db,
        action="EVIDENCE_SUBMITTED",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"evidence_type": ev_type.value, "nos_id": body.nos_id, "worker_id": str(worker.id)},
    )

    return EvidenceResponse.model_validate(record)


@router.post(
    "/upload/{worker_id}",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an evidence file",
)
async def upload_evidence_file(
    worker_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: str = Form("OTHER"),
    source_type: str = Form("SELF"),
    description: str = Form(...),
    nos_id: Optional[str] = Form(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    id_q = _match_id(worker_id)
    worker_doc = await db.workers.find_one({"$or": [{"id": id_q}, {"user_id": id_q}]})
    if not worker_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(worker_doc)
    if current_user.role == UserRole.WORKER and str(worker.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        ev_type = EvidenceType(evidence_type)
        src_type = EvidenceSourceType(source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    saved = await storage_service.save_upload(file, worker.id)

    now = datetime.now(timezone.utc)
    record = EvidenceRecord(
        id=uuid.uuid4(),
        worker_id=worker.id,
        uploaded_by_id=current_user.id,
        evidence_type=ev_type.value,
        source_type=src_type.value,
        description=description,
        nos_id=nos_id or None,
        file_path=saved["file_path"],
        file_name=saved["file_name"],
        file_size_bytes=saved["file_size_bytes"],
        mime_type=saved["mime_type"],
        content_hash=saved["content_hash"],
        verification_status=EvidenceVerificationStatus.UNVERIFIED.value,
        created_at=now,
        updated_at=now,
    )
    doc = record.to_mongo()
    await db.evidence.insert_one(doc)

    await audit_service.record_event(
        db,
        action="EVIDENCE_FILE_UPLOADED",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"file_name": saved["file_name"], "size": saved["file_size_bytes"], "worker_id": str(worker.id)},
    )

    return EvidenceResponse.model_validate(record)


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get an evidence record by ID",
)
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    id_q = _match_id(evidence_id)
    doc = await db.evidence.find_one({"id": id_q})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    record = EvidenceRecord.from_mongo(doc)
    worker_doc = await db.workers.find_one({"id": _match_id(record.worker_id)})
    worker_user_id = worker_doc.get("user_id") if worker_doc else None
    _assert_evidence_access(record, current_user, worker_user_id)
    return EvidenceResponse.model_validate(record)


@router.patch(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Update evidence metadata",
)
async def update_evidence(
    evidence_id: uuid.UUID,
    body: EvidenceUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    id_q = _match_id(evidence_id)
    doc = await db.evidence.find_one({"id": id_q})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    record = EvidenceRecord.from_mongo(doc)
    worker_doc = await db.workers.find_one({"id": _match_id(record.worker_id)})
    worker_user_id = worker_doc.get("user_id") if worker_doc else None
    _assert_evidence_access(record, current_user, worker_user_id)

    if record.verification_status not in (
        EvidenceVerificationStatus.UNVERIFIED.value,
        EvidenceVerificationStatus.PENDING_REVIEW.value,
        "PENDING",
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update already verified or rejected evidence",
        )

    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    await db.evidence.update_one({"id": id_q}, {"$set": update_data})

    updated_doc = await db.evidence.find_one({"id": id_q})
    return EvidenceResponse.model_validate(EvidenceRecord.from_mongo(updated_doc))


@router.post(
    "/{evidence_id}/verify",
    response_model=EvidenceResponse,
    summary="Verify or reject an evidence record (assessors only)",
)
async def verify_evidence(
    evidence_id: uuid.UUID,
    body: EvidenceVerifyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> EvidenceResponse:
    id_q = _match_id(evidence_id)
    doc = await db.evidence.find_one({"id": id_q})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    record = EvidenceRecord.from_mongo(doc)

    raw_status = body.verification_status.upper().strip()
    if raw_status in ("NEEDS_INFO", "PENDING"):
        raw_status = "PENDING_REVIEW"

    try:
        new_status = EvidenceVerificationStatus(raw_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {body.verification_status}",
        )

    now = datetime.now(timezone.utc)
    update_data = {
        "verification_status": new_status.value,
        "verified_by_id": current_user.id,
        "verified_at": now,
        "verification_notes": body.verification_notes,
        "updated_at": now,
    }
    await db.evidence.update_one({"id": id_q}, {"$set": update_data})
    updated_doc = await db.evidence.find_one({"id": id_q})

    await audit_service.record_event(
        db,
        action=f"EVIDENCE_{new_status.value}",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={
            "new_status": new_status.value,
            "previous_status": record.verification_status,
            "verification_notes": body.verification_notes,
            "worker_id": str(record.worker_id),
        },
    )

    return EvidenceResponse.model_validate(EvidenceRecord.from_mongo(updated_doc))


@router.get(
    "/{evidence_id}/download",
    summary="Download an evidence file",
)
async def download_evidence_file(
    evidence_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    id_q = _match_id(evidence_id)
    doc = await db.evidence.find_one({"id": id_q})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    record = EvidenceRecord.from_mongo(doc)
    worker_doc = await db.workers.find_one({"id": _match_id(record.worker_id)})
    worker_user_id = worker_doc.get("user_id") if worker_doc else None
    _assert_evidence_access(record, current_user, worker_user_id)

    if not record.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file attached to this evidence record")

    try:
        resolved = storage_service.resolve_file_path(record.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on storage")

    return FileResponse(
        path=str(resolved),
        filename=record.file_name or "evidence_file",
        media_type=record.mime_type or "application/octet-stream",
    )
