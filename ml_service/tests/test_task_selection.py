"""
Tests: Module 5 — Adaptive Assessment & Task Selection
"""

import pytest
from app.algorithms.task_selector import (
    task_value,
    rank_tasks,
    select_next_task,
    select_task_variant,
    should_continue_assessment,
)
from app.services.task_selection_service import (
    get_next_task,
    rank_all_tasks,
    get_task_variant,
    check_continuation,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

DEMO_COMPETENCY_STATES = {
    "DEMO_NOS_004": {
        "importance": 1.0,
        "mandatory": True,
        "evidence_confidence": 0.35,
        "evidence_coverage": 0.2,
        "weight": 1.0,
    },
    "DEMO_NOS_005": {
        "importance": 0.9,
        "mandatory": True,
        "evidence_confidence": 0.55,
        "evidence_coverage": 0.4,
        "weight": 0.9,
    },
    "DEMO_NOS_009": {
        "importance": 0.5,
        "mandatory": False,
        "evidence_confidence": None,
        "evidence_coverage": 0.8,
        "weight": 0.5,
    },
}

DEMO_TASKS = [
    {
        "id": "T_ISOLATION",
        "title": "Safe Isolation",
        "description": "Isolate a circuit safely",
        "duration_minutes": 8,
        "mandatory": True,
        "active": True,
        "randomizable": False,
        "nos_coverage": [
            {"nos_id": "DEMO_NOS_004", "coverage": 1.0},
            {"nos_id": "DEMO_NOS_009", "coverage": 0.5},
        ],
    },
    {
        "id": "T_FAULT",
        "title": "Fault Diagnosis",
        "description": "Diagnose an electrical fault",
        "duration_minutes": 10,
        "mandatory": True,
        "active": True,
        "randomizable": True,
        "nos_coverage": [
            {"nos_id": "DEMO_NOS_005", "coverage": 1.0},
            {"nos_id": "DEMO_NOS_009", "coverage": 0.3},
        ],
        "variants": [
            {"id": "V1", "code": "F01", "label": "Open circuit", "parameters": {}},
            {"id": "V2", "code": "F02", "label": "Faulty switch", "parameters": {}},
            {"id": "V3", "code": "F03", "label": "Disconnected terminal", "parameters": {}},
        ],
    },
    {
        "id": "T_SAFETY",
        "title": "Safety Demonstration",
        "description": "PPE and hazard identification",
        "duration_minutes": 6,
        "mandatory": False,
        "active": True,
        "randomizable": False,
        "nos_coverage": [{"nos_id": "DEMO_NOS_009", "coverage": 1.0}],
    },
    {
        "id": "T_INACTIVE",
        "title": "Inactive Task",
        "description": "Not in use",
        "duration_minutes": 5,
        "mandatory": False,
        "active": False,  # Should be excluded
        "nos_coverage": [],
    },
]


# ---------------------------------------------------------------------------
# Uncertainty calculation
# ---------------------------------------------------------------------------

class TestUncertainty:
    def test_uncertainty_from_confidence(self):
        state = {"evidence_confidence": 0.6, "evidence_coverage": 0.5}
        # uncertainty = 1 - confidence = 0.4
        score, _ = task_value(
            {"id": "T", "title": "T", "duration_minutes": 10, "active": True, "mandatory": False,
             "nos_coverage": [{"nos_id": "NOS_A", "coverage": 1.0}]},
            {"NOS_A": {"importance": 1.0, "evidence_confidence": 0.6, "evidence_coverage": 0.5, "mandatory": False}},
        )
        assert score > 0.0

    def test_uncertainty_fallback_to_coverage(self):
        # When confidence is None, fallback = 1 - coverage
        score, _ = task_value(
            {"id": "T", "title": "T", "duration_minutes": 10, "active": True, "mandatory": False,
             "nos_coverage": [{"nos_id": "NOS_A", "coverage": 1.0}]},
            {"NOS_A": {"importance": 1.0, "evidence_confidence": None, "evidence_coverage": 0.3, "mandatory": False}},
        )
        assert score > 0.0


# ---------------------------------------------------------------------------
# Task value formula
# ---------------------------------------------------------------------------

class TestTaskValue:
    def test_task_with_no_nos_coverage_has_zero_value(self):
        task = {"id": "T", "title": "T", "duration_minutes": 10, "active": True,
                "mandatory": False, "nos_coverage": []}
        score, _ = task_value(task, DEMO_COMPETENCY_STATES)
        assert score == 0.0

    def test_high_uncertainty_increases_value(self):
        # NOS with very low confidence → high uncertainty → high task value
        high_uncertainty_state = {
            "NOS_HIGH": {
                "importance": 1.0,
                "mandatory": True,
                "evidence_confidence": 0.0,
                "evidence_coverage": 0.0,
                "weight": 1.0,
            }
        }
        task = {"id": "T", "title": "T", "duration_minutes": 5, "active": True,
                "mandatory": True,
                "nos_coverage": [{"nos_id": "NOS_HIGH", "coverage": 1.0}]}
        score, _ = task_value(task, high_uncertainty_state)
        assert score > 0.1  # meaningful value expected

    def test_shorter_duration_increases_value(self):
        state = {"NOS_A": {"importance": 1.0, "evidence_confidence": 0.5,
                            "evidence_coverage": 0.5, "mandatory": True, "weight": 1.0}}
        task_short = {"id": "T1", "title": "T", "duration_minutes": 5, "active": True,
                      "mandatory": False, "nos_coverage": [{"nos_id": "NOS_A", "coverage": 1.0}]}
        task_long = {"id": "T2", "title": "T", "duration_minutes": 20, "active": True,
                     "mandatory": False, "nos_coverage": [{"nos_id": "NOS_A", "coverage": 1.0}]}
        score_short, _ = task_value(task_short, state)
        score_long, _ = task_value(task_long, state)
        assert score_short > score_long


# ---------------------------------------------------------------------------
# Task ranking
# ---------------------------------------------------------------------------

class TestTaskRanking:
    def test_inactive_task_excluded(self):
        ranked = rank_tasks(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        ids = [t["id"] for t in ranked]
        assert "T_INACTIVE" not in ids

    def test_ranked_descending(self):
        ranked = rank_tasks(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        scores = [t["priority_score"] for t in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_excluded_tasks_not_in_results(self):
        ranked = rank_tasks(DEMO_TASKS, DEMO_COMPETENCY_STATES, exclude_task_ids=["T_ISOLATION"])
        ids = [t["id"] for t in ranked]
        assert "T_ISOLATION" not in ids

    def test_reason_list_populated(self):
        ranked = rank_tasks(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        for task in ranked:
            assert isinstance(task["reason"], list)


# ---------------------------------------------------------------------------
# Next task selection
# ---------------------------------------------------------------------------

class TestNextTaskSelection:
    def test_returns_single_task(self):
        task = select_next_task(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        assert task is not None
        assert "id" in task
        assert "priority_score" in task

    def test_selection_is_deterministic(self):
        t1 = select_next_task(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        t2 = select_next_task(DEMO_TASKS, DEMO_COMPETENCY_STATES)
        assert t1["id"] == t2["id"]

    def test_returns_none_when_all_excluded(self):
        exclude_all = [t["id"] for t in DEMO_TASKS if t.get("active", True)]
        task = select_next_task(DEMO_TASKS, DEMO_COMPETENCY_STATES, exclude_task_ids=exclude_all)
        assert task is None


# ---------------------------------------------------------------------------
# Task variant selection
# ---------------------------------------------------------------------------

class TestTaskVariantSelection:
    def test_variant_selected_from_available(self):
        fault_task = next(t for t in DEMO_TASKS if t["id"] == "T_FAULT")
        variant = select_task_variant(fault_task, seed=42)
        assert variant is not None
        assert "code" in variant

    def test_excluded_variant_not_selected(self):
        fault_task = next(t for t in DEMO_TASKS if t["id"] == "T_FAULT")
        for _ in range(20):
            variant = select_task_variant(fault_task, exclude_variant_codes=["F01"], seed=None)
            assert variant is None or variant["code"] != "F01"

    def test_all_excluded_returns_none(self):
        fault_task = next(t for t in DEMO_TASKS if t["id"] == "T_FAULT")
        variant = select_task_variant(fault_task, exclude_variant_codes=["F01", "F02", "F03"])
        assert variant is None

    def test_task_without_variants_returns_none(self):
        task = next(t for t in DEMO_TASKS if t["id"] == "T_ISOLATION")
        variant = select_task_variant(task)
        assert variant is None

    def test_seeded_selection_reproducible(self):
        fault_task = next(t for t in DEMO_TASKS if t["id"] == "T_FAULT")
        v1 = select_task_variant(fault_task, seed=99)
        v2 = select_task_variant(fault_task, seed=99)
        assert v1 == v2


# ---------------------------------------------------------------------------
# Early stopping
# ---------------------------------------------------------------------------

class TestEarlyStopping:
    def test_should_continue_when_mandatory_gaps(self):
        states = [
            {"nos_id": "DEMO_NOS_004", "mandatory": True, "evidence_coverage": 0.3},
            {"nos_id": "DEMO_NOS_005", "mandatory": True, "evidence_coverage": 0.9},
        ]
        result = should_continue_assessment(states, coverage_threshold=0.8)
        assert result["should_continue"] is True
        assert "DEMO_NOS_004" in result["mandatory_gaps"]

    def test_should_stop_when_all_covered(self):
        states = [
            {"nos_id": "DEMO_NOS_004", "mandatory": True, "evidence_coverage": 0.9},
            {"nos_id": "DEMO_NOS_005", "mandatory": True, "evidence_coverage": 0.85},
        ]
        result = should_continue_assessment(states, coverage_threshold=0.8)
        assert result["should_continue"] is False
        assert result["mandatory_gaps"] == []


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestTaskSelectionService:
    def test_service_get_next_task(self):
        states = [
            {"nos_id": "DEMO_NOS_004", "mandatory": True, "importance": 1.0,
             "weight": 1.0, "evidence_confidence": None, "evidence_coverage": 0.2,
             "competency_score": 0},
        ]
        task = get_next_task(states)
        assert task is not None

    def test_service_rank_all_tasks(self):
        states = [
            {"nos_id": "DEMO_NOS_004", "mandatory": True, "importance": 1.0,
             "weight": 1.0, "evidence_confidence": 0.4, "evidence_coverage": 0.3,
             "competency_score": 60},
        ]
        ranked = rank_all_tasks(states)
        assert len(ranked) > 0

    def test_service_get_variant(self):
        result = get_task_variant("TASK_004", seed=42)
        assert result is not None
        assert result["variant"] is not None

    def test_service_check_continuation(self):
        states = [
            {"nos_id": "DEMO_NOS_004", "mandatory": True, "importance": 1.0,
             "weight": 1.0, "evidence_confidence": None, "evidence_coverage": 0.2,
             "competency_score": 0},
        ]
        result = check_continuation(states)
        assert "should_continue" in result
