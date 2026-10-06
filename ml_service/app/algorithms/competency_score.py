"""
KaushalTwin ML Service — Competency Scoring Algorithm
Module 3: Competency Twin & Evidence Graph Engine
"""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Weighted criterion scoring
# ---------------------------------------------------------------------------

def weighted_competency_score(
    criteria: list[dict],
) -> dict:
    """
    Calculate the weighted competency score from criterion results.

    Each criterion dict must contain:
        score  : float  — observed score
        weight : float  — importance weight (must be > 0)
        max_score : float — maximum possible score (default 5)

    Formula:
        weighted_score = SUM(score × weight) / SUM(weight)
        normalised     = (weighted_score / max_score) × 100

    Returns a dict with:
        raw_score         — weighted average (0 to max_score)
        competency_score  — normalised 0-100 int
        total_weight      — sum of weights used
        observed_count    — number of criteria that were actually scored
        max_possible      — maximum possible score used for normalisation
    """
    if not criteria:
        return {
            "raw_score": 0.0,
            "competency_score": 0,
            "total_weight": 0.0,
            "observed_count": 0,
            "max_possible": 5.0,
        }

    total_weight = 0.0
    weighted_sum = 0.0
    observed_count = 0
    max_score = 5.0  # default; overridden per-criterion if present

    for c in criteria:
        weight = float(c.get("weight", 0))
        score = c.get("score")
        c_max = float(c.get("max_score", 5.0))

        if weight <= 0:
            continue
        if score is None:
            # Criterion present but not yet scored — skip
            continue

        score = float(score)
        # Clamp score to valid range
        score = max(0.0, min(score, c_max))
        max_score = c_max  # last wins — assumes homogeneous max_score

        weighted_sum += score * weight
        total_weight += weight
        observed_count += 1

    if total_weight == 0.0:
        return {
            "raw_score": 0.0,
            "competency_score": 0,
            "total_weight": 0.0,
            "observed_count": 0,
            "max_possible": max_score,
        }

    raw_score = weighted_sum / total_weight
    competency_score = int(round((raw_score / max_score) * 100))
    competency_score = max(0, min(100, competency_score))

    return {
        "raw_score": round(raw_score, 4),
        "competency_score": competency_score,
        "total_weight": round(total_weight, 4),
        "observed_count": observed_count,
        "max_possible": max_score,
    }


# ---------------------------------------------------------------------------
# Evidence coverage
# ---------------------------------------------------------------------------

def compute_evidence_coverage(
    criteria: list[dict],
    required_criteria_ids: Optional[list[str]] = None,
) -> float:
    """
    Calculate evidence coverage — the proportion of the competency that has
    actually been observed/assessed.

    If required_criteria_ids is given: coverage = observed required / total required.
    Otherwise: coverage = weight_of_scored / total_weight.

    Returns a float in [0.0, 1.0].
    """
    if not criteria:
        return 0.0

    if required_criteria_ids:
        required = set(required_criteria_ids)
        observed_required = sum(
            1 for c in criteria
            if c.get("id") in required and c.get("score") is not None
        )
        return round(observed_required / len(required), 4) if required else 0.0

    # Weight-based coverage
    total_weight = sum(float(c.get("weight", 0)) for c in criteria if float(c.get("weight", 0)) > 0)
    scored_weight = sum(
        float(c.get("weight", 0))
        for c in criteria
        if c.get("score") is not None and float(c.get("weight", 0)) > 0
    )
    if total_weight == 0.0:
        return 0.0
    return round(scored_weight / total_weight, 4)


# ---------------------------------------------------------------------------
# Competency status
# ---------------------------------------------------------------------------

def derive_competency_status(
    competency_score: int,
    evidence_coverage: float,
    evidence_confidence: Optional[float] = None,
) -> str:
    """
    Determine a simple competency status from available data.

    Allowed statuses (current module scope):
        UNASSESSED       — no evidence at all
        IN_PROGRESS      — some evidence but assessment incomplete
        EVIDENCE_AVAILABLE — meaningful evidence exists

    COMMIT / ABSTAIN belong to future Module 7 and are NOT produced here.
    """
    if evidence_coverage == 0.0 and competency_score == 0:
        return "UNASSESSED"
    if evidence_coverage >= 0.8:
        return "EVIDENCE_AVAILABLE"
    return "IN_PROGRESS"
