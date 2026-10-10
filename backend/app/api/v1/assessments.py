"""
KaushalTwin Backend — API Routes: Assessments + Tasks + ML integration + Decisions + Reports

POST   /api/v1/assessments                                    — Create assessment
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
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    MLServiceError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["Assessments"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_assessment_or_404(
    assessment_id: uuid.UUID, db: AsyncSession
) -> Assessment:
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment


def _assert_assessor_owns(assessment: Assessment, current_user: User) -> None:
    """Only the assigned assessor or admin can modify an assessment."""
    if current_user.role == UserRole.ADMIN:
        return
    if assessment.assessor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _assert_can_view(assessment: Assessment, current_user: User, worker: Optional[WorkerProfile] = None) -> None:
    if current_user.role in (UserRole.ADMIN, UserRole.ASSESSOR):
        return
    # Worker role: only own assessments
    if worker and worker.user_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assessment",
)
async def create_assessment(
    body: AssessmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    # Validate worker exists
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == body.worker_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")

    assessment = Assessment(
        id=uuid.uuid4(),
        worker_id=body.worker_id,
        assessor_id=current_user.id,
        trade=body.trade,
        notes=body.notes,
        status=AssessmentLifecycle.DRAFT,
    )
    db.add(assessment)
    await db.flush()

    await audit_service.record_event(
        db,
        action="ASSESSMENT_CREATED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"worker_id": str(body.worker_id), "trade": body.trade},
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentListResponse:
    query = select(Assessment)
    if current_user.role == UserRole.ASSESSOR:
        query = query.where(Assessment.assessor_id == current_user.id)
    if status_filter:
        try:
            lc = AssessmentLifecycle(status_filter.upper())
            query = query.where(Assessment.status == lc)
        except ValueError:
            pass

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    result = await db.execute(query.offset(skip).limit(limit))
    assessments = result.scalars().all()

    return AssessmentListResponse(
        items=[AssessmentResponse.model_validate(a) for a in assessments],
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AssessmentResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_can_view(assessment, current_user)
    return AssessmentResponse.model_validate(assessment)


@router.patch(
    "/{assessment_id}",
    response_model=AssessmentResponse,
    summary="Update assessment notes",
)
async def update_assessment(
    assessment_id: uuid.UUID,
    body: AssessmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(assessment, field, value)

    return AssessmentResponse.model_validate(assessment)


@router.post(
    "/{assessment_id}/start",
    response_model=AssessmentResponse,
    summary="Start an assessment (DRAFT → IN_PROGRESS)",
)
async def start_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    if assessment.status != AssessmentLifecycle.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment is {assessment.status.value}, not DRAFT",
        )

    assessment.status = AssessmentLifecycle.IN_PROGRESS
    assessment.started_at = datetime.now(timezone.utc)

    await audit_service.record_event(
        db,
        action="ASSESSMENT_STARTED",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
    )

    return AssessmentResponse.model_validate(assessment)


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentResponse,
    summary="Mark assessment ready for review (IN_PROGRESS → READY_FOR_REVIEW)",
)
async def complete_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AssessmentResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    if assessment.status != AssessmentLifecycle.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment must be IN_PROGRESS to mark complete",
        )

    assessment.status = AssessmentLifecycle.READY_FOR_REVIEW
    assessment.completed_at = datetime.now(timezone.utc)

    await audit_service.record_event(
        db,
        action="ASSESSMENT_READY_FOR_REVIEW",
        entity_type="Assessment",
        entity_id=str(assessment.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
    )

    return AssessmentResponse.model_validate(assessment)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a task to an assessment (assessor-assigned)",
)
async def create_task(
    assessment_id: uuid.UUID,
    body: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> TaskResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    try:
        src = TaskSelectionSource(body.selection_source.upper())
    except ValueError:
        src = TaskSelectionSource.ASSESSOR_ASSIGNED

    task = AssessmentTask(
        id=uuid.uuid4(),
        assessment_id=assessment_id,
        assessor_id=current_user.id,
        title=body.title,
        description=body.description,
        target_nos_id=body.target_nos_id,
        selection_source=src,
        evaluation_criteria=(
            json.dumps(body.evaluation_criteria)
            if body.evaluation_criteria is not None
            else None
        ),
        status=TaskStatus.PENDING,
    )
    db.add(task)
    await db.flush()

    return TaskResponse.model_validate(task)


@router.get(
    "/{assessment_id}/tasks",
    response_model=list[TaskResponse],
    summary="List tasks for an assessment",
)
async def list_tasks(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[TaskResponse]:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_can_view(assessment, current_user)

    result = await db.execute(
        select(AssessmentTask).where(AssessmentTask.assessment_id == assessment_id)
    )
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.post(
    "/{assessment_id}/tasks/{task_id}/result",
    response_model=TaskResponse,
    summary="Submit a result for an assessment task",
)
async def submit_task_result(
    assessment_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskResultRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> TaskResponse:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    result = await db.execute(
        select(AssessmentTask).where(
            AssessmentTask.id == task_id,
            AssessmentTask.assessment_id == assessment_id,
        )
    )
    task: AssessmentTask | None = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already completed",
        )

    task.score = body.score
    task.assessor_comments = body.assessor_comments
    task.evidence_references = (
        json.dumps(body.evidence_references) if body.evidence_references else None
    )
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)

    await audit_service.record_event(
        db,
        action="TASK_RESULT_SUBMITTED",
        entity_type="AssessmentTask",
        entity_id=str(task.id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={"score": body.score, "assessment_id": str(assessment_id)},
    )

    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# ML Integration
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/analyze",
    response_model=AIRunResponse,
    summary="Run the full ML pipeline for this assessment",
)
async def analyze_assessment(
    assessment_id: uuid.UUID,
    body: MLAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> AIRunResponse:
    """
    Triggers the unified ML pipeline.
    Persists the full input snapshot and ML response.
    Does NOT overwrite existing assessor decisions.
    """
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    # Load worker profile
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == assessment.worker_id)
    )
    worker: WorkerProfile | None = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=500, detail="Worker profile not found")

    # Gather evidence for this worker
    ev_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.worker_id == assessment.worker_id)
    )
    evidence_records = ev_result.scalars().all()

    # Build transcript from worker profile
    transcript = (
        f"{worker.experience_summary or ''} "
        f"{worker.education_summary or ''}"
    ).strip() or f"Worker in {worker.trade} with {worker.years_of_experience} years experience"

    # Build evidence list for ML (use metadata only)
    ml_evidence = [
        {
            "source": rec.source_type.value,
            "supports": rec.verification_status.value == "VERIFIED",
            "notes": rec.description,
        }
        for rec in evidence_records
    ]

    # Safe input snapshot (no secrets)
    input_snapshot = {
        "worker_id": str(worker.id),
        "trade": assessment.trade,
        "language": body.language,
        "evidence_count": len(ml_evidence),
        "include_calibration": body.include_calibration,
    }

    # Create a pending AI run record
    ai_run = AIAssessmentRun(
        id=uuid.uuid4(),
        worker_id=assessment.worker_id,
        assessment_id=assessment_id,
        triggered_by_id=current_user.id,
        run_status=RunStatus.RUNNING,
        input_snapshot_json=json.dumps(input_snapshot, default=str),
    )
    db.add(ai_run)
    await db.flush()

    # Call the ML service
    try:
        ml_response = await run_pipeline(
            worker_id=str(worker.id),
            transcript=transcript,
            language=body.language,
            trade=assessment.trade,
            evidence=ml_evidence,
            claim=body.claim_for_explanation,
        )
        ai_run.ml_response_json = json.dumps(ml_response, default=str)
        ai_run.run_status = RunStatus.COMPLETED

        # Denormalize top-level recommendation
        cert = ml_response.get("certification_recommendation") or {}
        ai_run.recommendation = cert.get("recommendation")

        await audit_service.record_event(
            db,
            action="ML_RUN_COMPLETED",
            entity_type="AIAssessmentRun",
            entity_id=str(ai_run.id),
            actor_user_id=current_user.id,
            actor_label=current_user.email,
            metadata={
                "assessment_id": str(assessment_id),
                "recommendation": ai_run.recommendation,
            },
        )

    except MLServiceError as exc:
        ai_run.run_status = RunStatus.FAILED
        ai_run.error_detail = str(exc)
        await audit_service.record_event(
            db,
            action="ML_RUN_FAILED",
            entity_type="AIAssessmentRun",
            entity_id=str(ai_run.id),
            actor_user_id=current_user.id,
            actor_label=current_user.email,
            metadata={"error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service error: {exc}",
        )

    return AIRunResponse(
        id=ai_run.id,
        assessment_id=ai_run.assessment_id,
        worker_id=ai_run.worker_id,
        run_status=ai_run.run_status.value,
        recommendation=ai_run.recommendation,
        ml_response=json.loads(ai_run.ml_response_json) if ai_run.ml_response_json else None,
        error_detail=ai_run.error_detail,
        created_at=ai_run.created_at,
    )


@router.get(
    "/{assessment_id}/ai-results",
    response_model=list[AIRunResponse],
    summary="Get all AI analysis runs for this assessment",
)
async def get_ai_results(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AIRunResponse]:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_can_view(assessment, current_user)

    result = await db.execute(
        select(AIAssessmentRun)
        .where(AIAssessmentRun.assessment_id == assessment_id)
        .order_by(AIAssessmentRun.created_at.desc())
    )
    runs = result.scalars().all()

    return [
        AIRunResponse(
            id=r.id,
            assessment_id=r.assessment_id,
            worker_id=r.worker_id,
            run_status=r.run_status.value,
            recommendation=r.recommendation,
            ml_response=json.loads(r.ml_response_json) if r.ml_response_json else None,
            error_detail=r.error_detail,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.post(
    "/{assessment_id}/recommend-next-task",
    response_model=NextTaskRecommendationResponse,
    summary="Get AI recommendation for the next assessment task",
)
async def recommend_next_task(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> NextTaskRecommendationResponse:
    """
    Calls the ML adaptive assessment module to recommend the next task.
    The recommendation is persisted as a PENDING AI-recommended task.
    The assessor must explicitly accept, modify, or skip it.
    """
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    # Get the latest completed AI run to get competency states
    result = await db.execute(
        select(AIAssessmentRun)
        .where(
            AIAssessmentRun.assessment_id == assessment_id,
            AIAssessmentRun.run_status == RunStatus.COMPLETED,
        )
        .order_by(AIAssessmentRun.created_at.desc())
        .limit(1)
    )
    latest_run: AIAssessmentRun | None = result.scalar_one_or_none()

    competency_states: list[dict] = []
    if latest_run and latest_run.ml_response_json:
        try:
            ml_data = json.loads(latest_run.ml_response_json)
            twin = ml_data.get("competency_twin", {})
            competency_states = twin.get("competencies", [])
        except (json.JSONDecodeError, AttributeError):
            pass

    if not competency_states:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No competency data available. Run /analyze first.",
        )

    # Get already-completed task IDs to exclude
    completed_result = await db.execute(
        select(AssessmentTask.ml_task_id)
        .where(
            AssessmentTask.assessment_id == assessment_id,
            AssessmentTask.status == TaskStatus.COMPLETED,
            AssessmentTask.ml_task_id.isnot(None),
        )
    )
    completed_task_ids = [r[0] for r in completed_result.all() if r[0]]

    # Create an AI run record for this next-task call
    ai_run = AIAssessmentRun(
        id=uuid.uuid4(),
        worker_id=assessment.worker_id,
        assessment_id=assessment_id,
        triggered_by_id=current_user.id,
        run_status=RunStatus.RUNNING,
        input_snapshot_json=json.dumps({
            "action": "next_task",
            "competency_states_count": len(competency_states),
            "excluded_tasks": completed_task_ids,
        }),
    )
    db.add(ai_run)
    await db.flush()

    try:
        ml_response = await ml_get_next_task(
            competency_states=competency_states,
            exclude_task_ids=completed_task_ids,
        )
        ai_run.ml_response_json = json.dumps(ml_response, default=str)
        ai_run.run_status = RunStatus.COMPLETED

    except MLServiceError as exc:
        ai_run.run_status = RunStatus.FAILED
        ai_run.error_detail = str(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML service error: {exc}",
        )

    # Persist the AI-recommended task if one was selected
    persisted_task_id: Optional[uuid.UUID] = None
    selected = ml_response.get("selected_task")
    if selected:
        reasons_json = json.dumps(ml_response.get("reason", []))
        task = AssessmentTask(
            id=uuid.uuid4(),
            assessment_id=assessment_id,
            assessor_id=current_user.id,
            ml_task_id=selected.get("id"),
            title=selected.get("title", "AI Recommended Task"),
            description=selected.get("description"),
            target_nos_id=(
                selected.get("nos_coverage", [{}])[0].get("nos_id")
                if selected.get("nos_coverage")
                else None
            ),
            selection_source=TaskSelectionSource.AI_RECOMMENDED,
            ai_priority_score=ml_response.get("priority_score"),
            ai_reasons=reasons_json,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        persisted_task_id = task.id

    return NextTaskRecommendationResponse(
        ai_run_id=ai_run.id,
        task_id=persisted_task_id,
        selected_task=selected,
        priority_score=ml_response.get("priority_score", 0.0),
        reason=ml_response.get("reason", []),
        alternatives=ml_response.get("alternatives", []),
        note=ml_response.get(
            "note",
            "Task selection is AI-assisted. Assessor must review before assigning.",
        ),
    )


@router.get(
    "/{assessment_id}/recommendation",
    response_model=Optional[dict],
    summary="Get the latest AI certification recommendation",
)
async def get_recommendation(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Optional[dict]:
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_can_view(assessment, current_user)

    result = await db.execute(
        select(AIAssessmentRun)
        .where(
            AIAssessmentRun.assessment_id == assessment_id,
            AIAssessmentRun.run_status == RunStatus.COMPLETED,
        )
        .order_by(AIAssessmentRun.created_at.desc())
        .limit(1)
    )
    run: AIAssessmentRun | None = result.scalar_one_or_none()
    if not run:
        return None

    ml_data = json.loads(run.ml_response_json) if run.ml_response_json else {}
    return {
        "ai_run_id": str(run.id),
        "run_created_at": run.created_at.isoformat(),
        "recommendation": run.recommendation,
        "certification_recommendation": ml_data.get("certification_recommendation"),
        "abstention_decision": ml_data.get("abstention_decision"),
        "note": "This is an AI recommendation only. The human assessor makes the final decision.",
    }


# ---------------------------------------------------------------------------
# Assessor Decision
# ---------------------------------------------------------------------------

@router.post(
    "/{assessment_id}/decision",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record the assessor's final decision (independent of AI output)",
)
async def record_decision(
    assessment_id: uuid.UUID,
    body: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_assessor),
) -> DecisionResponse:
    """
    Record the assessor's independent final decision.
    This record is separate from the AI run — the AI output is never overwritten.
    """
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_assessor_owns(assessment, current_user)

    try:
        action = DecisionAction(body.action.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {body.action}",
        )

    decision = AssessorDecision(
        id=uuid.uuid4(),
        assessment_id=assessment_id,
        ai_run_id=body.ai_run_id,
        assessor_id=current_user.id,
        action=action,
        comments=body.comments,
        modified_recommendation=body.modified_recommendation,
    )
    db.add(decision)

    # Update assessment status if appropriate
    if action in (DecisionAction.ACCEPT_RECOMMENDATION, DecisionAction.MODIFY_RECOMMENDATION):
        assessment.status = AssessmentLifecycle.REVIEWED

    await db.flush()

    await audit_service.record_event(
        db,
        action=f"ASSESSOR_DECISION_{action.value}",
        entity_type="Assessment",
        entity_id=str(assessment_id),
        actor_user_id=current_user.id,
        actor_label=current_user.email,
        metadata={
            "decision_id": str(decision.id),
            "action": action.value,
            "ai_run_id": str(body.ai_run_id) if body.ai_run_id else None,
        },
    )

    return DecisionResponse(
        id=decision.id,
        assessment_id=decision.assessment_id,
        assessor_id=decision.assessor_id,
        action=decision.action.value,
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AssessmentReport:
    """
    Assembles a complete structured report from persisted data.
    Does not call the ML service — uses stored AI run data only.
    Unavailable information is explicitly marked as null/absent.
    """
    assessment = await _get_assessment_or_404(assessment_id, db)
    _assert_can_view(assessment, current_user)

    # Worker
    wp_result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.id == assessment.worker_id)
    )
    worker = wp_result.scalar_one_or_none()

    # Evidence
    ev_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.worker_id == assessment.worker_id)
    )
    evidence_records = ev_result.scalars().all()

    # Tasks
    task_result = await db.execute(
        select(AssessmentTask).where(AssessmentTask.assessment_id == assessment_id)
    )
    tasks = task_result.scalars().all()

    # AI runs
    run_result = await db.execute(
        select(AIAssessmentRun)
        .where(AIAssessmentRun.assessment_id == assessment_id)
        .order_by(AIAssessmentRun.created_at.desc())
    )
    ai_runs = run_result.scalars().all()

    # Latest decision
    dec_result = await db.execute(
        select(AssessorDecision)
        .where(AssessorDecision.assessment_id == assessment_id)
        .order_by(AssessorDecision.created_at.desc())
        .limit(1)
    )
    latest_decision = dec_result.scalar_one_or_none()

    # Audit trail
    audit_result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type.in_(["Assessment", "AIAssessmentRun", "AssessmentTask"]),
            AuditEvent.entity_id.in_(
                [str(assessment_id)]
                + [str(r.id) for r in ai_runs]
                + [str(t.id) for t in tasks]
            ),
        )
        .order_by(AuditEvent.created_at.asc())
    )
    audit_events = audit_result.scalars().all()

    # Latest completed AI run for recommendation
    latest_run = next(
        (r for r in ai_runs if r.run_status == RunStatus.COMPLETED), None
    )
    latest_rec = None
    if latest_run and latest_run.ml_response_json:
        ml_data = json.loads(latest_run.ml_response_json)
        latest_rec = {
            "ai_run_id": str(latest_run.id),
            "recommendation": latest_run.recommendation,
            "certification_recommendation": ml_data.get("certification_recommendation"),
            "abstention_decision": ml_data.get("abstention_decision"),
            "skill_gap_analysis": ml_data.get("skill_gap_analysis"),
        }

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
            "status": assessment.status.value,
            "trade": assessment.trade,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        },
        evidence_summary={
            "total": len(evidence_records),
            "verified": sum(1 for e in evidence_records if e.verification_status.value == "VERIFIED"),
            "unverified": sum(1 for e in evidence_records if e.verification_status.value == "UNVERIFIED"),
            "rejected": sum(1 for e in evidence_records if e.verification_status.value == "REJECTED"),
            "records": [
                {
                    "id": str(e.id),
                    "evidence_type": e.evidence_type.value,
                    "source_type": e.source_type.value,
                    "description": e.description,
                    "nos_id": e.nos_id,
                    "verification_status": e.verification_status.value,
                }
                for e in evidence_records
            ],
        },
        ai_runs=[
            {
                "id": str(r.id),
                "status": r.run_status.value,
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
                "status": t.status.value,
                "selection_source": t.selection_source.value,
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
                "action": latest_decision.action.value,
                "comments": latest_decision.comments,
                "modified_recommendation": latest_decision.modified_recommendation,
                "created_at": latest_decision.created_at.isoformat(),
            }
            if latest_decision
            else None
        ),
        audit_timeline=[
            {
                "id": str(e.id),
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "actor": e.actor_label,
                "timestamp": e.created_at.isoformat(),
            }
            for e in audit_events
        ],
    )
