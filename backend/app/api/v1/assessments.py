"""
KaushalTwin Backend — API Routes: Assessments + Tasks + ML integration + Decisions + Reports

POST   /api/v1/assessments                                    — Create or resume assessment
GET    /api/v1/assessments                                    — List assessments
GET    /api/v1/assessments/{id}                               — Get assessment
PATCH  /api/v1/assessments/{id}                               — Update assessment
POST   /api/v1/assessments/{id}/start                         — Start assessment
POST   /api/v1/assessments/{id}/complete                      — Mark ready for review
POST   /api/v1/assessments/{id}/tasks                         — Add manual task
GET    /api/v1/assessments/{id}/tasks                         — List tasks
POST   /api/v1/assessments/{id}/tasks/{task_id}/result        — Submit task result
POST   /api/v1/assessments/{id}/analyze                       — Run ML pipeline
GET    /api/v1/assessments/{id}/ai-results                    — Get all AI runs
POST   /api/v1/assessments/{id}/recommend-next-task           — AI next-best-task
POST   /api/v1/assessments/{id}/check-evidence                — Check evidence sufficiency
GET    /api/v1/assessments/{id}/recommendation                — Get latest AI recommendation
POST   /api/v1/assessments/{id}/decision                      — Assessor final decision
GET    /api/v1/assessments/{id}/report                        — Structured JSON report
"""

from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.dependencies import get_db, get_current_active_user, require_assessor
from app.db.models.user import User, UserRole
from app.db.models.worker import WorkerProfile
from app.db.models.assessment import (
    Assessment,
    AssessmentLifecycle,
    AssessmentTask,
    TaskStatus,
    TaskSelectionSource,
)
from app.db.models.evidence import EvidenceRecord
from app.db.models.ai_run import AIAssessmentRun, RunStatus
from app.db.models.decision import AssessorDecision, DecisionAction
from app.db.models.audit import AuditEvent
from app.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentUpdateRequest,
    AssessmentResponse,
    AssessmentListResponse,
    TaskCreateRequest,
    TaskResultRequest,
    TaskResponse,
)
from app.schemas.ml import (
    MLAnalysisRequest,
    AIRunResponse,
    NextTaskRecommendationResponse,
    DecisionRequest,
    DecisionResponse,
    AssessmentReport,
)
from app.services import audit_service
from app.services.ml_client import (
    run_pipeline,
    get_next_task as ml_get_next_task,
    check_abstention as ml_check_abstention,
    analyze_evidence as ml_analyze_evidence,
    MLServiceError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["Assessments"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _match_id(val: uuid.UUID | str) -> dict:
    s_val = str(val)
    try:
        u_val = uuid.UUID(s_val)
        return {"$in": [s_val, u_val]}
    except (ValueError, TypeError):
        return {"$eq": s_val}


async def _get_assessment_or_404(
    assessment_id: uuid.UUID, db: AsyncIOMotorDatabase
) -> Assessment:
    id_q = _match_id(assessment_id)
    doc = await db.assessments.find_one({"id": id_q})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return Assessment.from_mongo(doc)


def _assert_assessor_owns(assessment: Assessment, current_user: User) -> None:
    """Only the assigned assessor or admins can modify an assessment."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.ASSESSOR and str(assessment.assessor_id) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _assert_can_view(assessment: Assessment, current_user: User, worker: Optional[WorkerProfile] = None) -> None:
    if current_user.role in (UserRole.ADMIN, UserRole.ASSESSOR):
        return
    if worker and str(worker.user_id) == str(current_user.id):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or resume an assessment",
)
async def create_assessment(
    body: AssessmentCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    worker_id_q = _match_id(body.worker_id)
    worker_doc = await db.workers.find_one({"$or": [{"id": worker_id_q}, {"user_id": worker_id_q}]})
    if not worker_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    worker = WorkerProfile.from_mongo(worker_doc)

    # Check for active existing assessment to prevent duplicate creation and support resuming
    existing = await db.assessments.find_one({
        "worker_id": _match_id(worker.id),
        "trade": body.trade,
        "status": {"$in": ["DRAFT", "ENROLLED", "IN_PROGRESS", "READY_FOR_REVIEW"]},
    })
    if existing:
        logger.info("Resuming existing active assessment %s for worker %s (%s)", existing["id"], worker.id, body.trade)
        return AssessmentResponse.model_validate(Assessment.from_mongo(existing))

    now = datetime.now(timezone.utc)
    assessment = Assessment(
        id=uuid.uuid4(),
        worker_id=worker.id,
        assessor_id=current_user.id,
        trade=body.trade,
        notes=body.notes,
        status="DRAFT",
        created_at=now,
        updated_at=now,
    )
    doc = assessment.to_mongo()
    await db.assessments.insert_one(doc)

    await audit_service.record_event(
        db,
        action="ASSESSMENT_CREATED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"worker_id": str(worker.id), "trade": body.trade},
    )

    return AssessmentResponse.model_validate(assessment)


@router.get(
    "",
    response_model=AssessmentListResponse,
    summary="List assessments",
)
async def list_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    worker_id: Optional[uuid.UUID] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentListResponse:
    query: dict = {}
    if worker_id:
        query["worker_id"] = _match_id(worker_id)
    if status_filter:
        query["status"] = status_filter.upper()

    total = await db.assessments.count_documents(query)
    cursor = db.assessments.find(query).skip(skip).limit(limit).sort("created_at", -1)
    items = []
    async for doc in cursor:
        items.append(AssessmentResponse.model_validate(Assessment.from_mongo(doc)))

    return AssessmentListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Get an assessment by ID",
)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AssessmentResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    w_q = _match_id(assessment.worker_id)
    worker_doc = await db.workers.find_one({"id": w_q})
    worker = WorkerProfile.from_mongo(worker_doc) if worker_doc else None
    _assert_can_view(assessment, current_user, worker)
    return AssessmentResponse.model_validate(assessment)


@router.patch(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update assessment notes",
)
async def update_assessment(
    assessment_id: uuid.UUID,
    body: AssessmentUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    id_q = _match_id(assessment_id)
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)
    await db.assessments.update_one({"id": id_q}, {"$set": update_data})

    updated_doc = await db.assessments.find_one({"id": id_q})
    return AssessmentResponse.model_validate(Assessment.from_mongo(updated_doc))


@router.post(
    "/{assessment_id}/start",
    response_model=AssessmentResponse,
    summary="Start an assessment (DRAFT → IN_PROGRESS)",
)
async def start_assessment(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    id_q = _match_id(assessment_id)
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    status_str = assessment.status if isinstance(assessment.status, str) else assessment.status.value
    if status_str not in ("DRAFT", "ENROLLED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment is {status_str}, not DRAFT or ENROLLED",
        )

    now = datetime.now(timezone.utc)
    await db.assessments.update_one(
        {"id": id_q},
        {"$set": {"status": "IN_PROGRESS", "started_at": now, "updated_at": now}},
    )

    await audit_service.record_event(
        db,
        action="ASSESSMENT_STARTED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"worker_id": str(assessment.worker_id), "trade": assessment.trade},
    )

    updated_doc = await db.assessments.find_one({"id": id_q})
    return AssessmentResponse.model_validate(Assessment.from_mongo(updated_doc))


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentResponse,
    summary="Mark assessment ready for assessor review (IN_PROGRESS → READY_FOR_REVIEW)",
)
async def complete_assessment(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    id_q = _match_id(assessment_id)
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    status_str = assessment.status if isinstance(assessment.status, str) else assessment.status.value
    if status_str != "IN_PROGRESS":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment must be IN_PROGRESS to complete; currently {status_str}",
        )

    now = datetime.now(timezone.utc)
    await db.assessments.update_one(
        {"id": id_q},
        {"$set": {"status": "READY_FOR_REVIEW", "completed_at": now, "updated_at": now}},
    )

    await audit_service.record_event(
        db,
        action="ASSESSMENT_COMPLETED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"worker_id": str(assessment.worker_id), "trade": assessment.trade},
    )

    updated_doc = await db.assessments.find_one({"id": id_q})
    return AssessmentResponse.model_validate(Assessment.from_mongo(updated_doc))


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an evaluation task to an assessment",
)
async def create_task(
    assessment_id: uuid.UUID,
    body: TaskCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> TaskResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    task = AssessmentTask(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        title=body.title,
        description=body.description,
        target_nos_id=body.target_nos_id,
        selection_source=body.selection_source,
        evaluation_criteria=json.dumps(body.evaluation_criteria) if body.evaluation_criteria else None,
        status="PENDING",
    )
    doc = task.to_mongo()
    await db.assessment_tasks.insert_one(doc)

    await audit_service.record_event(
        db,
        action="TASK_CREATED",
        entity_type="AssessmentTask",
        entity_id=str(task.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"title": task.title, "source": body.selection_source, "assessment_id": str(assessment.id)},
    )

    return TaskResponse.model_validate(task)


@router.get(
    "/{assessment_id}/tasks",
    response_model=list[TaskResponse],
    summary="List all evaluation tasks for an assessment",
)
async def list_tasks(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TaskResponse]:
    assessment = await _get_assessment_or_404(assessment_id, db)
    worker_doc = await db.workers.find_one({"id": _match_id(assessment.worker_id)})
    worker = WorkerProfile.from_mongo(worker_doc) if worker_doc else None
    _assert_can_view(assessment, current_user, worker)

    cursor = db.assessment_tasks.find({"assessment_id": _match_id(assessment_id)})
    tasks = []
    async for doc in cursor:
        tasks.append(TaskResponse.model_validate(AssessmentTask.from_mongo(doc)))
    return tasks


@router.post(
    "/{assessment_id}/tasks/{task_id}/result",
    response_model=TaskResponse,
    summary="Submit evaluation result for a task",
)
async def submit_task_result(
    assessment_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskResultRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> TaskResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    task_id_q = _match_id(task_id)
    asm_id_q = _match_id(assessment_id)
    task_doc = await db.assessment_tasks.find_one(
        {"id": task_id_q, "assessment_id": asm_id_q}
    )
    if not task_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task_doc.get("status") == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task has already been evaluated",
        )

    now = datetime.now(timezone.utc)
    ev_refs = json.dumps(body.evidence_references) if body.evidence_references else None
    update_data = {
        "status": "COMPLETED",
        "score": body.score,
        "assessor_comments": body.assessor_comments,
        "evidence_references": ev_refs,
        "completed_at": now,
    }
    await db.assessment_tasks.update_one({"id": task_id_q}, {"$set": update_data})

    await audit_service.record_event(
        db,
        action="TASK_EVALUATED",
        entity_type="AssessmentTask",
        entity_id=str(task_doc.get("id")),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"score": body.score, "assessment_id": str(assessment.id)},
    )

    updated_doc = await db.assessment_tasks.find_one({"id": task_id_q})
    return TaskResponse.model_validate(AssessmentTask.from_mongo(updated_doc))


# ---------------------------------------------------------------------------
# ML Pipeline Execution
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/analyze",
    response_model=AIRunResponse,
    summary="Trigger the AI assessment pipeline for this assessment",
)
async def analyze_assessment(
    assessment_id: uuid.UUID,
    body: MLAnalysisRequest = MLAnalysisRequest(),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AIRunResponse:
    """
    Run the unified ML pipeline in-process or over HTTP.
    Stores the full result and recommendation.
    Never auto-certifies: output is purely advisory.
    """
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    worker_doc = await db.workers.find_one({"id": _match_id(assessment.worker_id)})
    if not worker_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    worker = WorkerProfile.from_mongo(worker_doc)

    # Gather evidence
    ev_cursor = db.evidence.find({"worker_id": _match_id(assessment.worker_id)})
    evidence_records = []
    async for e in ev_cursor:
        evidence_records.append(e)

    # Gather completed tasks
    task_cursor = db.assessment_tasks.find({
        "assessment_id": _match_id(assessment_id),
        "status": "COMPLETED",
    })
    completed_tasks = []
    async for t in task_cursor:
        completed_tasks.append(t)

    # Build transcript from worker data
    transcript = (
        body.claim_for_explanation
        or worker.work_narrative
        or worker.experience_summary
        or f"{worker.trade} practitioner with {worker.years_of_experience} years of hands-on experience."
    )

    evidence_payload = [
        {
            "evidence_id": str(e["id"]),
            "type": e.get("evidence_type", "OTHER"),
            "verified": e.get("verification_status") == "VERIFIED",
        }
        for e in evidence_records
    ]

    assessor_scores = [
        {
            "task_id": str(t["id"]),
            "nos_id": t.get("target_nos_id") or "GENERAL",
            "score": t.get("score", 0.0),
        }
        for t in completed_tasks
    ]

    ai_run = AIAssessmentRun(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        worker_id=assessment.worker_id,
        run_status="RUNNING",
    )
    await db.ai_runs.insert_one(ai_run.to_mongo())

    try:
        pipeline_result = await run_pipeline(
            worker_id=str(assessment.worker_id),
            transcript=transcript,
            language=body.language,
            trade=worker.trade,
            evidence=evidence_payload,
            assessor_scores=assessor_scores,
            claim=body.claim_for_explanation,
        )

        cert_rec = pipeline_result.get("certification_recommendation") or {}
        recommendation_str = cert_rec.get("recommendation") or "REQUIRES_ASSESSOR_REVIEW"

        now = datetime.now(timezone.utc)
        await db.ai_runs.update_one(
            {"id": _match_id(ai_run.id)},
            {
                "$set": {
                    "run_status": "COMPLETED",
                    "recommendation": recommendation_str,
                    "ml_response": pipeline_result,
                    "created_at": now,
                }
            },
        )

        # Transition assessment to READY_FOR_REVIEW
        await db.assessments.update_one(
            {"id": _match_id(assessment_id)},
            {"$set": {"status": "READY_FOR_REVIEW", "updated_at": now}},
        )

        await audit_service.record_event(
            db,
            action="AI_ANALYSIS_COMPLETED",
            entity_type="AIAssessmentRun",
            entity_id=str(ai_run.id),
            actor_user_id=current_user.id,
            actor_label=current_user.email,
            actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            metadata={"recommendation": recommendation_str, "assessment_id": str(assessment.id)},
        )

        updated_run = await db.ai_runs.find_one({"id": _match_id(ai_run.id)})
        return AIRunResponse.model_validate(AIAssessmentRun.from_mongo(updated_run))

    except MLServiceError as exc:
        now = datetime.now(timezone.utc)
        await db.ai_runs.update_one(
            {"id": _match_id(ai_run.id)},
            {"$set": {"run_status": "FAILED", "error_detail": str(exc), "created_at": now}},
        )
        await audit_service.record_event(
            db,
            action="AI_ANALYSIS_FAILED",
            entity_type="AIAssessmentRun",
            entity_id=str(ai_run.id),
            actor_user_id=current_user.id,
            actor_label=current_user.email,
            actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            metadata={"error": str(exc), "assessment_id": str(assessment.id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service error: {exc}",
        )


@router.get(
    "/{assessment_id}/ai-results",
    response_model=list[AIRunResponse],
    summary="Get all AI assessment runs for an assessment",
)
async def get_ai_results(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AIRunResponse]:
    assessment = await _get_assessment_or_404(assessment_id, db)
    worker_doc = await db.workers.find_one({"id": _match_id(assessment.worker_id)})
    worker = WorkerProfile.from_mongo(worker_doc) if worker_doc else None
    _assert_can_view(assessment, current_user, worker)

    cursor = db.ai_runs.find({"assessment_id": _match_id(assessment_id)}).sort("created_at", -1)
    runs = []
    async for doc in cursor:
        runs.append(AIRunResponse.model_validate(AIAssessmentRun.from_mongo(doc)))
    return runs


@router.post(
    "/{assessment_id}/recommend-next-task",
    response_model=NextTaskRecommendationResponse,
    summary="Get AI recommendation for the next evaluation task",
)
async def recommend_next_task(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> NextTaskRecommendationResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    latest_run = await db.ai_runs.find_one(
        {"assessment_id": _match_id(assessment_id), "run_status": "COMPLETED"},
        sort=[("created_at", -1)],
    )

    competency_states: list[dict] = []
    if latest_run and latest_run.get("ml_response"):
        twin = latest_run["ml_response"].get("competency_twin", {})
        competency_states = twin.get("competencies", [])

    if not competency_states:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No competency data available. Run /analyze first.",
        )

    task_cursor = db.assessment_tasks.find({"assessment_id": _match_id(assessment_id)})
    existing_ml_ids = []
    async for t in task_cursor:
        if t.get("ml_task_id"):
            existing_ml_ids.append(t["ml_task_id"])

    try:
        rec_data = await ml_get_next_task(
            competency_states=competency_states,
            exclude_task_ids=existing_ml_ids,
        )
    except MLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service error: {exc}",
        )

    selected = rec_data.get("selected_task")
    persisted_task_id = None
    if selected:
        persisted_task = AssessmentTask(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            title=selected.get("title", "Recommended Task"),
            description=selected.get("description"),
            target_nos_id=selected.get("nos_coverage", [{}])[0].get("nos_id") if selected.get("nos_coverage") else selected.get("nos_id"),
            ml_task_id=selected.get("task_id") or selected.get("id"),
            selection_source="AI_RECOMMENDED",
            ai_priority_score=rec_data.get("priority_score"),
            ai_reasons=json.dumps(rec_data.get("reason", [])),
            status="PENDING",
        )
        await db.assessment_tasks.insert_one(persisted_task.to_mongo())
        persisted_task_id = persisted_task.id

    ai_run_id = uuid.uuid4()
    await db.ai_runs.insert_one(
        AIAssessmentRun(
            id=ai_run_id,
            assessment_id=assessment.id,
            worker_id=assessment.worker_id,
            run_status="COMPLETED",
            recommendation=selected.get("task_id") if selected else "NO_TASK_RECOMMENDED",
            ml_response=rec_data,
        ).to_mongo()
    )

    return NextTaskRecommendationResponse(
        ai_run_id=ai_run_id,
        task_id=persisted_task_id,
        selected_task=selected,
        priority_score=rec_data.get("priority_score", 0.0),
        reason=rec_data.get("reason", []),
        alternatives=rec_data.get("alternatives", []),
        note="Advisory recommendation. Assessor decides whether to administer this task.",
    )


@router.post(
    "/{assessment_id}/check-evidence",
    summary="Check evidence sufficiency and abstention recommendation",
)
async def check_evidence_sufficiency(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> dict:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    ev_cursor = db.evidence.find({"worker_id": _match_id(assessment.worker_id)})
    evidence_records = []
    async for e in ev_cursor:
        evidence_records.append({
            "evidence_id": str(e["id"]),
            "type": e.get("evidence_type", "OTHER"),
            "verified": e.get("verification_status") == "VERIFIED",
            "description": e.get("description", ""),
        })

    competencies = [
        {"nos_id": "DEMO_NOS_001", "name": "Basic Operations", "score": 75},
        {"nos_id": "DEMO_NOS_002", "name": "Safety Protocols", "score": 80},
    ]

    try:
        ev_analysis = (
            await ml_analyze_evidence(evidence_records)
            if evidence_records
            else {
                "source_features": [],
                "support_score": 0.0,
                "contradict_score": 0.0,
                "independent_sources": 0,
                "conflict": False,
                "conflict_reason": None,
            }
        )
        abs_check = await ml_check_abstention(
            worker_id=str(assessment.worker_id),
            competencies=competencies,
            evidence_records=evidence_records if evidence_records else None,
        )
    except MLServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service error: {exc}",
        )

    ai_run_id = uuid.uuid4()
    await db.ai_runs.insert_one(
        AIAssessmentRun(
            id=ai_run_id,
            assessment_id=assessment.id,
            worker_id=assessment.worker_id,
            run_status="COMPLETED",
            recommendation=abs_check.get("status", "ABSTAIN"),
            ml_response={"evidence_analysis": ev_analysis, "abstention_check": abs_check},
        ).to_mongo()
    )

    return {
        "ai_run_id": ai_run_id,
        "evidence_analysis": ev_analysis,
        "abstention_check": abs_check,
    }


@router.get(
    "/{assessment_id}/recommendation",
    summary="Get latest AI recommendation and assessor decision state",
)
async def get_latest_recommendation(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    assessment = await _get_assessment_or_404(assessment_id, db)
    worker_doc = await db.workers.find_one({"id": _match_id(assessment.worker_id)})
    worker = WorkerProfile.from_mongo(worker_doc) if worker_doc else None
    _assert_can_view(assessment, current_user, worker)

    latest_run = await db.ai_runs.find_one(
        {"assessment_id": _match_id(assessment_id), "run_status": "COMPLETED"},
        sort=[("created_at", -1)],
    )

    latest_decision_doc = await db.decisions.find_one(
        {"assessment_id": _match_id(assessment_id)},
        sort=[("created_at", -1)],
    )
    decision_dict = None
    if latest_decision_doc:
        decision_dict = {
            "id": str(latest_decision_doc.get("id")),
            "action": latest_decision_doc.get("action"),
            "comments": latest_decision_doc.get("comments"),
            "modified_recommendation": latest_decision_doc.get("modified_recommendation"),
            "assessor_id": str(latest_decision_doc.get("assessor_id")),
            "decided_at": latest_decision_doc.get("created_at"),
        }

    if not latest_run:
        return {
            "assessment_id": str(assessment.id),
            "has_recommendation": False,
            "message": "No completed AI analysis runs found. Trigger /analyze first.",
            "recommendation": None,
            "decision": decision_dict,
        }

    ml_data = latest_run.get("ml_response") or {}
    return {
        "assessment_id": str(assessment.id),
        "has_recommendation": True,
        "ai_run_id": str(latest_run["id"]),
        "recommendation": latest_run.get("recommendation"),
        "certification_recommendation": ml_data.get("certification_recommendation"),
        "abstention_decision": ml_data.get("abstention_decision"),
        "skill_gap_analysis": ml_data.get("skill_gap_analysis"),
        "analyzed_at": latest_run.get("created_at"),
        "decision": decision_dict,
        "note": "AI recommendations are advisory only. The human assessor makes the final decision.",
    }


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/decision",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record assessor final certification decision",
)
async def record_decision(
    assessment_id: uuid.UUID,
    body: DecisionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> DecisionResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    raw_action = body.action.strip()
    action_map = {
        "PARTIAL_CERTIFICATION": "MODIFY_RECOMMENDATION",
        "REJECT_CERTIFICATION": "REJECT_RECOMMENDATION",
        "REQUEST_REASSESSMENT": "REQUEST_MORE_EVIDENCE",
    }
    normalized_action = action_map.get(raw_action, raw_action)

    try:
        action = DecisionAction(normalized_action)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {body.action}",
        )

    decision = AssessorDecision(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        ai_run_id=body.ai_run_id,
        assessor_id=current_user.id,
        action=action.value,
        comments=body.comments,
        modified_recommendation=body.modified_recommendation,
    )
    await db.decisions.insert_one(decision.to_mongo())

    now = datetime.now(timezone.utc)
    id_q = _match_id(assessment_id)
    if action in (DecisionAction.ACCEPT_RECOMMENDATION, DecisionAction.MODIFY_RECOMMENDATION):
        await db.assessments.update_one(
            {"id": id_q},
            {"$set": {"status": "REVIEWED", "completed_at": now, "updated_at": now}},
        )
    elif action == DecisionAction.REJECT_RECOMMENDATION:
        await db.assessments.update_one(
            {"id": id_q},
            {"$set": {"status": "COMPLETED", "completed_at": now, "updated_at": now}},
        )
    elif action == DecisionAction.REQUEST_MORE_EVIDENCE:
        await db.assessments.update_one(
            {"id": id_q},
            {"$set": {"status": "IN_PROGRESS", "updated_at": now}},
        )

    await audit_service.record_event(
        db,
        action="ASSESSOR_DECISION_RECORDED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={
            "decision_id": str(decision.id),
            "action": action.value,
            "ai_run_id": str(body.ai_run_id) if body.ai_run_id else None,
            "comments": body.comments,
        },
    )

    return DecisionResponse(
        id=decision.id,
        assessment_id=decision.assessment_id,
        assessor_id=decision.assessor_id,
        action=decision.action,
        comments=decision.comments,
        modified_recommendation=decision.modified_recommendation,
        ai_run_id=decision.ai_run_id,
        created_at=decision.created_at,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@router.get(
    "/{assessment_id}/report",
    response_model=AssessmentReport,
    summary="Generate a structured JSON assessment report",
)
async def get_report(
    assessment_id: uuid.UUID,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AssessmentReport:
    assessment = await _get_assessment_or_404(assessment_id, db)
    w_q = _match_id(assessment.worker_id)
    worker_doc = await db.workers.find_one({"id": w_q})
    worker = WorkerProfile.from_mongo(worker_doc) if worker_doc else None
    _assert_can_view(assessment, current_user, worker)

    # Evidence
    ev_cursor = db.evidence.find({"worker_id": w_q})
    evidence_records = []
    async for e in ev_cursor:
        evidence_records.append(EvidenceRecord.from_mongo(e))

    # Tasks
    task_cursor = db.assessment_tasks.find({"assessment_id": _match_id(assessment_id)})
    tasks = []
    async for t in task_cursor:
        tasks.append(AssessmentTask.from_mongo(t))

    # AI runs
    run_cursor = db.ai_runs.find({"assessment_id": _match_id(assessment_id)}).sort("created_at", -1)
    ai_runs = []
    async for r in run_cursor:
        ai_runs.append(AIAssessmentRun.from_mongo(r))

    # Latest decision
    latest_decision_doc = await db.decisions.find_one(
        {"assessment_id": _match_id(assessment_id)},
        sort=[("created_at", -1)],
    )
    latest_decision = AssessorDecision.from_mongo(latest_decision_doc) if latest_decision_doc else None

    # Audit trail
    entity_ids = [str(assessment.id)] + [str(r.id) for r in ai_runs] + [str(t.id) for t in tasks]
    audit_cursor = db.audit_events.find({
        "entity_type": {"$in": ["Assessment", "AIAssessmentRun", "AssessmentTask"]},
        "entity_id": {"$in": entity_ids},
    }).sort("timestamp", 1)
    audit_events = []
    async for a in audit_cursor:
        audit_events.append(a)

    latest_run = next((r for r in ai_runs if r.run_status in ("COMPLETED", "SUCCESS")), None)
    latest_rec = None
    if latest_run and latest_run.ml_response:
        ml_data = latest_run.ml_response
        latest_rec = {
            "ai_run_id": str(latest_run.id),
            "recommendation": latest_run.recommendation,
            "certification_recommendation": ml_data.get("certification_recommendation"),
            "abstention_decision": ml_data.get("abstention_decision"),
            "skill_gap_analysis": ml_data.get("skill_gap_analysis"),
        }

    status_str = assessment.status if isinstance(assessment.status, str) else assessment.status.value

    # Record report generation audit event
    await audit_service.record_event(
        db,
        action="DOSSIER_GENERATED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        actor_role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        metadata={"trade": assessment.trade, "has_decision": latest_decision is not None},
    )

    return AssessmentReport(
        generated_at=datetime.now(timezone.utc),
        worker={
            "id": str(worker.id) if worker else None,
            "full_name": worker.full_name if worker else "Unknown",
            "trade": worker.trade if worker else assessment.trade,
            "years_of_experience": worker.years_of_experience if worker else None,
            "experience_summary": worker.experience_summary if worker else None,
        },
        assessment={
            "id": str(assessment.id),
            "status": status_str,
            "trade": assessment.trade,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        },
        evidence_summary={
            "total": len(evidence_records),
            "verified": sum(1 for e in evidence_records if e.verification_status == "VERIFIED"),
            "unverified": sum(1 for e in evidence_records if e.verification_status in ("UNVERIFIED", "PENDING", "PENDING_REVIEW")),
            "rejected": sum(1 for e in evidence_records if e.verification_status == "REJECTED"),
            "records": [
                {
                    "id": str(e.id),
                    "evidence_type": e.evidence_type,
                    "source_type": e.source_type,
                    "description": e.description,
                    "nos_id": e.nos_id,
                    "verification_status": e.verification_status,
                }
                for e in evidence_records
            ],
        },
        ai_runs=[
            {
                "id": str(r.id),
                "status": r.run_status,
                "recommendation": r.recommendation,
                "created_at": r.created_at.isoformat(),
                "error": r.error_detail,
            }
            for r in ai_runs
        ],
        tasks=[
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status,
                "selection_source": t.selection_source,
                "target_nos_id": t.target_nos_id,
                "score": t.score,
                "assessor_comments": t.assessor_comments,
            }
            for t in tasks
        ],
        latest_recommendation=latest_rec,
        latest_decision=(
            {
                "id": str(latest_decision.id),
                "action": latest_decision.action,
                "comments": latest_decision.comments,
                "modified_recommendation": latest_decision.modified_recommendation,
                "created_at": latest_decision.created_at.isoformat(),
            }
            if latest_decision
            else None
        ),
        audit_timeline=[
            {
                "id": str(e.get("id")),
                "action": e.get("action"),
                "entity_type": e.get("entity_type"),
                "entity_id": e.get("entity_id"),
                "actor": e.get("actor_label"),
                "timestamp": e.get("timestamp").isoformat() if isinstance(e.get("timestamp"), datetime) else str(e.get("timestamp")),
            }
            for e in audit_events
        ],
    )
