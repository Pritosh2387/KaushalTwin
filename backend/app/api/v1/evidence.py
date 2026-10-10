"""
KaushalTwin Backend — API Routes: Evidence

POST   /api/v1/evidence                           — Submit evidence metadata
POST   /api/v1/evidence/upload/{worker_id}        — Upload evidence file
GET    /api/v1/evidence/{evidence_id}             — Get evidence record
PATCH  /api/v1/evidence/{evidence_id}             — Update evidence metadata
POST   /api/v1/evidence/{evidence_id}/verify      — Verify or reject evidence (assessors)
"""

from __future__ import annotations

import json
import uuid
import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
)
from app.services import audit_service, storage_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evidence", tags=["Evidence"])


def _assert_evidence_access(record: EvidenceRecord, current_user: User) -> None:
    if current_user.role in (UserRole.ADMIN, UserRole.ASSESSOR):
        return
    if record.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit evidence metadata (without file)",
)
async def create_evidence(
    body: EvidenceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    """
    Submit evidence metadata.
    File upload is a separate step via /evidence/upload/{worker_id}.
    Uploaded evidence starts as UNVERIFIED — verification is a separate action.
    """
    # Validate worker exists
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == body.worker_id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    # Workers can only submit their own evidence
    if current_user.role == UserRole.WORKER and worker.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Validate enums
    try:
        ev_type = EvidenceType(body.evidence_type)
        src_type = EvidenceSourceType(body.source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    record = EvidenceRecord(
        id=uuid.uuid4(),
        worker_id=body.worker_id,
        assessment_id=body.assessment_id,
        uploaded_by_id=current_user.id,
        evidence_type=ev_type,
        source_type=src_type,
        description=body.description,
        nos_id=body.nos_id,
        verification_status=EvidenceVerificationStatus.UNVERIFIED,
        metadata_json=json.dumps(body.metadata_json) if body.metadata_json else None,
    )
    db.add(record)
    await db.flush()

    await audit_service.record_event(
        db,
        action="EVIDENCE_SUBMITTED",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"evidence_type": ev_type.value, "nos_id": body.nos_id},
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
    nos_id: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    """
    Upload a file and create the corresponding evidence metadata record.
    Files are stored server-side with UUID names.
    Evidence starts as UNVERIFIED.
    """
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    if current_user.role == UserRole.WORKER and worker.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        ev_type = EvidenceType(evidence_type)
        src_type = EvidenceSourceType(source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    saved = await storage_service.save_upload(file, worker_id)

    record = EvidenceRecord(
        id=uuid.uuid4(),
        worker_id=worker_id,
        uploaded_by_id=current_user.id,
        evidence_type=ev_type,
        source_type=src_type,
        description=description,
        nos_id=nos_id or None,
        file_path=saved["file_path"],
        file_name=saved["file_name"],
        file_size_bytes=saved["file_size_bytes"],
        mime_type=saved["mime_type"],
        content_hash=saved["content_hash"],
        verification_status=EvidenceVerificationStatus.UNVERIFIED,
    )
    db.add(record)
    await db.flush()

    await audit_service.record_event(
        db,
        action="EVIDENCE_FILE_UPLOADED",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"file_name": saved["file_name"], "size": saved["file_size_bytes"]},
    )

    return EvidenceResponse.model_validate(record)


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Get an evidence record by ID",
)
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    )
    record: EvidenceRecord | None = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    _assert_evidence_access(record, current_user)
    return EvidenceResponse.model_validate(record)


@router.patch(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    summary="Update evidence metadata",
)
async def update_evidence(
    evidence_id: uuid.UUID,
    body: EvidenceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EvidenceResponse:
    result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    )
    record: EvidenceRecord | None = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    _assert_evidence_access(record, current_user)

    # Only allow update if UNVERIFIED
    if record.verification_status != EvidenceVerificationStatus.UNVERIFIED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update verified or rejected evidence",
        )

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    return EvidenceResponse.model_validate(record)


@router.post(
    "/{evidence_id}/verify",
    response_model=EvidenceResponse,
    summary="Verify or reject an evidence record (assessors only)",
)
async def verify_evidence(
    evidence_id: uuid.UUID,
    body: EvidenceVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> EvidenceResponse:
    """
    Assessors can mark evidence as VERIFIED, REJECTED, or PENDING_REVIEW.
    This is an explicit assessor action — never automatic.
    """
    result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.id == evidence_id)
    )
    record: EvidenceRecord | None = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    try:
        new_status = EvidenceVerificationStatus(body.verification_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {body.verification_status}",
        )

    record.verification_status = new_status
    record.verified_by_id = current_user.id
    record.verification_notes = body.verification_notes

    await audit_service.record_event(
        db,
        action=f"EVIDENCE_{new_status.value}",
        entity_type="EvidenceRecord",
        entity_id=str(record.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"new_status": new_status.value},
    )

    return EvidenceResponse.model_validate(record)
