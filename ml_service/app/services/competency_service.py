"""
KaushalTwin ML Service — Competency Service
Module 3: Competency Twin & Competency Scoring
"""

from __future__ import annotations

from typing import Optional

from app.algorithms.competency_score import (
    weighted_competency_score,
    compute_evidence_coverage,
    derive_competency_status,
)


def score_competency(
    nos_id: str,
    criteria: list[dict],
    mandatory: bool = False,
    importance: float = 1.0,
    evidence_confidence: Optional[float] = None,
    required_criteria_ids: Optional[list[str]] = None,
) -> dict:
    """
    Calculate and return the full competency state for one NOS element.

    competency_score and evidence_confidence are kept separate.
    """
    scoring = weighted_competency_score(criteria)
    coverage = compute_evidence_coverage(criteria, required_criteria_ids)
    status = derive_competency_status(
        scoring["competency_score"], coverage, evidence_confidence
    )

    return {
        "nos_id": nos_id,
        "competency_score": scoring["competency_score"],
        "evidence_confidence": evidence_confidence,  # null until future module
        "evidence_coverage": coverage,
        "mandatory": mandatory,
        "importance": importance,
        "status": status,
        "scoring_detail": {
            "raw_score": scoring["raw_score"],
            "total_weight": scoring["total_weight"],
            "observed_count": scoring["observed_count"],
            "max_possible": scoring["max_possible"],
        },
    }


def build_competency_twin(
    worker_id: str,
    competencies_input: list[dict],
) -> dict:
    """
    Build a multi-NOS competency twin from a list of NOS assessment inputs.

    Input list format (per NOS):
        nos_id, criteria, mandatory, importance, evidence_confidence

    Returns the lightweight twin object.
    """
    competencies = []
    for comp in competencies_input:
        state = score_competency(
            nos_id=comp.get("nos_id", ""),
            criteria=comp.get("criteria", []),
            mandatory=comp.get("mandatory", False),
            importance=comp.get("importance", comp.get("weight", 1.0)),
            evidence_confidence=comp.get("evidence_confidence"),
            required_criteria_ids=comp.get("required_criteria_ids"),
        )
        competencies.append(state)

    # Overall summary
    mandatory_states = [c for c in competencies if c["mandatory"]]
    all_assessed = all(c["status"] != "UNASSESSED" for c in mandatory_states)
    overall_coverage = (
        round(
            sum(c["evidence_coverage"] for c in mandatory_states) / len(mandatory_states),
            4,
        )
        if mandatory_states
        else 0.0
    )

    return {
        "worker_id": worker_id,
        "competencies": competencies,
        "summary": {
            "total_nos": len(competencies),
            "mandatory_nos": len(mandatory_states),
            "all_mandatory_assessed": all_assessed,
            "mandatory_coverage_mean": overall_coverage,
        },
    }
