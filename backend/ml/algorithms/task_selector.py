"""
KaushalTwin ML Service — Adaptive Assessment Task Selector
Module 5: Adaptive Assessment / Next-Best-Task Engine

Selection is DETERMINISTIC and EXPLAINABLE.
No LLM, no random choice.
"""

from __future__ import annotations

import random
from typing import Optional


# ---------------------------------------------------------------------------
# Task value formula
# ---------------------------------------------------------------------------

def task_value(
    task: dict,
    competency_states: dict[str, dict],
) -> tuple[float, list[str]]:
    """
    Calculate the value of performing a given task for this worker right now.

    Formula:
        TaskValue = SUM( importance_i * uncertainty_i * coverage_i )
                    / duration_minutes

    Where:
        importance_i  = NOS weight (configured in NOS data)
        uncertainty_i = 1 - confidence  (if available)
                        1 - evidence_coverage  (fallback)
        coverage_i    = task-to-NOS coverage weight

    Returns (value_score, reason_list).
    """
    nos_coverage_list = task.get("nos_coverage", [])
    duration = max(float(task.get("duration_minutes", 10)), 1.0)

    if not nos_coverage_list:
        return 0.0, ["no NOS coverage defined for this task"]

    total_value = 0.0
    reasons: list[str] = []

    for nos_cov in nos_coverage_list:
        nos_id = nos_cov.get("nos_id", "")
        cov_weight = float(nos_cov.get("coverage", 0.0))
        state = competency_states.get(nos_id, {})

        importance = float(state.get("importance", state.get("weight", 0.5)))
        mandatory = state.get("mandatory", False)

        # Determine uncertainty
        confidence = state.get("evidence_confidence")
        coverage = float(state.get("evidence_coverage", 0.0))

        if confidence is not None:
            uncertainty = max(0.0, 1.0 - float(confidence))
        else:
            # Fallback: use 1 - evidence_coverage
            uncertainty = max(0.0, 1.0 - coverage)

        contribution = importance * uncertainty * cov_weight
        total_value += contribution

        # Build reason entries
        if mandatory and uncertainty > 0.5:
            reasons.append(f"{nos_id}: mandatory competency with high uncertainty")
        elif uncertainty > 0.5:
            reasons.append(f"{nos_id}: low evidence coverage ({coverage:.0%})")
        if cov_weight >= 0.8:
            reasons.append(f"{nos_id}: high NOS coverage by this task")

    score = round(total_value / duration, 6)

    # General reasons
    if task.get("mandatory"):
        reasons.append("task is mandatory in qualification")
    if duration <= 10:
        reasons.append(f"short duration ({int(duration)} min) for value delivered")

    return score, list(dict.fromkeys(reasons))  # deduplicate preserving order


# ---------------------------------------------------------------------------
# Task ranking
# ---------------------------------------------------------------------------

def rank_tasks(
    tasks: list[dict],
    competency_states: dict[str, dict],
    exclude_task_ids: Optional[list[str]] = None,
) -> list[dict]:
    """
    Rank all candidate tasks by their computed value score.

    Returns tasks sorted descending by value (highest priority first).
    Each task gets a 'priority_score' and 'reason' field added.
    """
    exclude = set(exclude_task_ids or [])
    scored: list[dict] = []

    for task in tasks:
        if not task.get("active", True):
            continue
        if task.get("id") in exclude:
            continue

        score, reasons = task_value(task, competency_states)
        scored.append({
            **task,
            "priority_score": score,
            "reason": reasons,
        })

    scored.sort(key=lambda t: t["priority_score"], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Select next task
# ---------------------------------------------------------------------------

def select_next_task(
    tasks: list[dict],
    competency_states: dict[str, dict],
    exclude_task_ids: Optional[list[str]] = None,
) -> Optional[dict]:
    """
    Select the single highest-value task for the current worker state.
    Returns None if no eligible tasks remain.
    """
    ranked = rank_tasks(tasks, competency_states, exclude_task_ids)
    if not ranked:
        return None
    return ranked[0]


# ---------------------------------------------------------------------------
# Task variant selection
# ---------------------------------------------------------------------------

def select_task_variant(
    task: dict,
    exclude_variant_codes: Optional[list[str]] = None,
    seed: Optional[int] = None,
) -> Optional[dict]:
    """
    Select a random variant from a task's variant list.
    Excludes already-used variants.

    Uses a seeded RNG for reproducibility in test mode.
    The physical board/environment handles the actual fault.
    """
    variants = task.get("variants", [])
    exclude = set(exclude_variant_codes or [])
    eligible = [v for v in variants if v.get("code") not in exclude]

    if not eligible:
        return None

    rng = random.Random(seed)
    return rng.choice(eligible)


# ---------------------------------------------------------------------------
# Early stopping placeholder
# ---------------------------------------------------------------------------

def should_continue_assessment(
    competency_states: list[dict],
    coverage_threshold: float = 0.8,
) -> dict:
    """
    Simple coverage-based early stopping check.

    Full probabilistic Commit/Abstain logic belongs to a FUTURE module.
    This function only checks whether mandatory competencies have sufficient coverage.

    Returns:
        should_continue : bool
        reason          : str
        mandatory_gaps  : list of NOS IDs with insufficient coverage
    """
    mandatory_gaps = [
        s["nos_id"]
        for s in competency_states
        if s.get("mandatory", False) and float(s.get("evidence_coverage", 0.0)) < coverage_threshold
    ]

    if mandatory_gaps:
        return {
            "should_continue": True,
            "reason": (
                f"{len(mandatory_gaps)} mandatory competency/competencies still lack "
                f"sufficient evidence coverage (threshold: {coverage_threshold:.0%})."
            ),
            "mandatory_gaps": mandatory_gaps,
        }

    return {
        "should_continue": False,
        "reason": "All mandatory competencies have reached the coverage threshold.",
        "mandatory_gaps": [],
    }
