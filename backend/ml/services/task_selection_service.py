"""
KaushalTwin ML Service — Task Selection Service
Module 5: Adaptive Assessment / Next-Best-Task Engine
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ml.algorithms.task_selector import (
    rank_tasks,
    select_next_task,
    select_task_variant,
    should_continue_assessment,
)

_TASKS_PATH = Path(__file__).parent.parent / "data" / "demo_tasks.json"
_tasks_cache: Optional[list[dict]] = None


def _load_tasks() -> list[dict]:
    global _tasks_cache
    if _tasks_cache is None:
        with open(_TASKS_PATH, encoding="utf-8") as f:
            _tasks_cache = json.load(f)
    return _tasks_cache


# ---------------------------------------------------------------------------
# Build competency state lookup from input
# ---------------------------------------------------------------------------

def _build_state_lookup(competency_states: list[dict]) -> dict[str, dict]:
    """Index competency states by nos_id for O(1) lookup in task scoring."""
    lookup: dict[str, dict] = {}
    for state in competency_states:
        nos_id = state.get("nos_id", "")
        if nos_id:
            lookup[nos_id] = state
    return lookup


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def get_next_task(
    competency_states: list[dict],
    available_tasks: Optional[list[dict]] = None,
    exclude_task_ids: Optional[list[str]] = None,
) -> Optional[dict]:
    """
    Select the single highest-value assessment task.

    Task selection is deterministic — no LLM, no randomness.
    """
    tasks = available_tasks or _load_tasks()
    state_lookup = _build_state_lookup(competency_states)
    return select_next_task(tasks, state_lookup, exclude_task_ids)


def rank_all_tasks(
    competency_states: list[dict],
    available_tasks: Optional[list[dict]] = None,
    exclude_task_ids: Optional[list[str]] = None,
) -> list[dict]:
    """Return all eligible tasks ranked by priority score."""
    tasks = available_tasks or _load_tasks()
    state_lookup = _build_state_lookup(competency_states)
    return rank_tasks(tasks, state_lookup, exclude_task_ids)


def get_task_variant(
    task_id: str,
    available_tasks: Optional[list[dict]] = None,
    exclude_variant_codes: Optional[list[str]] = None,
    seed: Optional[int] = None,
) -> Optional[dict]:
    """Select a task variant for a given task ID."""
    tasks = available_tasks or _load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        return None
    variant = select_task_variant(task, exclude_variant_codes, seed)
    return {"task_id": task_id, "task_title": task["title"], "variant": variant}


def check_continuation(
    competency_states: list[dict],
    coverage_threshold: float = 0.8,
) -> dict:
    """Check whether assessment should continue (simple coverage-based only)."""
    return should_continue_assessment(competency_states, coverage_threshold)
