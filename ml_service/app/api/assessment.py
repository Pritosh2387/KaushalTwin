"""
KaushalTwin ML Service — Assessment / Task Selection API
Module 5: Adaptive Assessment / Next-Best-Task Engine
"""

from fastapi import APIRouter, HTTPException
from app.schemas.assessment import (
    NextTaskRequest,
    NextTaskResponse,
    RankTasksRequest,
    RankTasksResponse,
    VariantSelectRequest,
    VariantSelectResponse,
    ContinuationRequest,
    ContinuationResponse,
    RankedTask,
    TaskVariant,
    TaskNOSCoverage,
)
from app.services.task_selection_service import (
    get_next_task,
    rank_all_tasks,
    get_task_variant,
    check_continuation,
)

router = APIRouter(prefix="/assessment", tags=["Module 5 · Adaptive Assessment"])


def _to_dict_list(items):
    if items is None:
        return None
    return [i.model_dump() for i in items]


def _parse_ranked(task: dict) -> RankedTask:
    return RankedTask(
        id=task["id"],
        title=task["title"],
        description=task.get("description", ""),
        duration_minutes=task.get("duration_minutes", 10),
        mandatory=task.get("mandatory", False),
        priority_score=task.get("priority_score", 0.0),
        reason=task.get("reason", []),
        nos_coverage=[
            TaskNOSCoverage(nos_id=c["nos_id"], coverage=c["coverage"])
            for c in task.get("nos_coverage", [])
        ],
    )


@router.post(
    "/next-task",
    response_model=NextTaskResponse,
    summary="Select the next highest-value assessment task",
)
def next_task_endpoint(request: NextTaskRequest) -> NextTaskResponse:
    """
    Deterministically select the most valuable assessment task for the worker's
    current competency state.

    Formula: TaskValue = SUM(importance × uncertainty × coverage) / duration

    Task selection does NOT use an LLM. It is fully explainable.
    """
    try:
        states = [s.model_dump() for s in request.competency_states]
        tasks = _to_dict_list(request.available_tasks)
        task = get_next_task(states, tasks, request.exclude_task_ids)
        ranked_all = rank_all_tasks(states, tasks, request.exclude_task_ids)

        if task is None:
            return NextTaskResponse(
                selected_task=None,
                priority_score=0.0,
                reason=["No eligible tasks available."],
                alternatives=[],
            )

        alternatives = [_parse_ranked(t) for t in ranked_all[1:4]]  # top 3 alternatives
        return NextTaskResponse(
            selected_task=_parse_ranked(task),
            priority_score=task.get("priority_score", 0.0),
            reason=task.get("reason", []),
            alternatives=alternatives,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "TASK_SELECTION_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/rank-tasks",
    response_model=RankTasksResponse,
    summary="Rank all available assessment tasks by priority score",
)
def rank_tasks_endpoint(request: RankTasksRequest) -> RankTasksResponse:
    """Return all eligible tasks ranked by their computed priority score."""
    try:
        states = [s.model_dump() for s in request.competency_states]
        tasks = _to_dict_list(request.available_tasks)
        ranked = rank_all_tasks(states, tasks, request.exclude_task_ids)
        return RankTasksResponse(
            ranked_tasks=[_parse_ranked(t) for t in ranked],
            count=len(ranked),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "RANKING_ERROR", "message": str(exc)}},
        ) from exc


@router.post(
    "/select-variant",
    response_model=VariantSelectResponse,
    summary="Select a task variant (e.g. fault type for fault-diagnosis task)",
)
def select_variant_endpoint(request: VariantSelectRequest) -> VariantSelectResponse:
    """
    Randomly select an unused task variant from a task's variant list.
    The physical board/environment implements the actual fault.
    """
    tasks = _to_dict_list(request.available_tasks)
    result = get_task_variant(
        task_id=request.task_id,
        available_tasks=tasks,
        exclude_variant_codes=request.exclude_variant_codes,
        seed=request.seed,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "TASK_NOT_FOUND", "message": f"Task '{request.task_id}' not found or has no eligible variants"}},
        )
    variant_data = result.get("variant")
    return VariantSelectResponse(
        task_id=result["task_id"],
        task_title=result["task_title"],
        variant=TaskVariant(**variant_data) if variant_data else None,
    )


@router.post(
    "/should-continue",
    response_model=ContinuationResponse,
    summary="Check if assessment should continue (simple coverage-based check)",
)
def should_continue_endpoint(request: ContinuationRequest) -> ContinuationResponse:
    """
    Simple coverage-based assessment continuation check.

    Full probabilistic Commit/Abstain logic is reserved for a future module.
    """
    states = [s.model_dump() for s in request.competency_states]
    result = check_continuation(states, request.coverage_threshold)
    return ContinuationResponse(**result)
