"""
Tests: Module 3 — Competency Twin & Scoring
"""

import pytest
from app.algorithms.competency_score import (
    weighted_competency_score,
    compute_evidence_coverage,
    derive_competency_status,
)
from app.services.competency_service import score_competency, build_competency_twin


# ---------------------------------------------------------------------------
# Algorithm tests
# ---------------------------------------------------------------------------

class TestWeightedCompetencyScore:
    def test_full_score_100(self):
        criteria = [
            {"score": 5, "weight": 0.5, "max_score": 5},
            {"score": 5, "weight": 0.5, "max_score": 5},
        ]
        result = weighted_competency_score(criteria)
        assert result["competency_score"] == 100

    def test_zero_score(self):
        criteria = [{"score": 0, "weight": 1.0, "max_score": 5}]
        result = weighted_competency_score(criteria)
        assert result["competency_score"] == 0

    def test_mixed_scores(self):
        # 4/5 = 80%, 5/5 = 100%, 4/5 = 80%
        criteria = [
            {"score": 4, "weight": 0.2, "max_score": 5},
            {"score": 5, "weight": 0.3, "max_score": 5},
            {"score": 4, "weight": 0.5, "max_score": 5},
        ]
        result = weighted_competency_score(criteria)
        assert result["competency_score"] == pytest.approx(84, abs=2)

    def test_empty_criteria_returns_zero(self):
        result = weighted_competency_score([])
        assert result["competency_score"] == 0

    def test_unscored_criteria_excluded(self):
        criteria = [
            {"score": 5, "weight": 0.5, "max_score": 5},
            {"score": None, "weight": 0.5, "max_score": 5},  # not yet scored
        ]
        result = weighted_competency_score(criteria)
        assert result["observed_count"] == 1
        assert result["competency_score"] == 100  # only scored criterion counts

    def test_score_clamped_to_100(self):
        criteria = [{"score": 6, "weight": 1.0, "max_score": 5}]  # over max
        result = weighted_competency_score(criteria)
        assert result["competency_score"] == 100

    def test_malformed_zero_weight_ignored(self):
        criteria = [
            {"score": 5, "weight": 0, "max_score": 5},  # weight=0 skipped
            {"score": 3, "weight": 1.0, "max_score": 5},
        ]
        result = weighted_competency_score(criteria)
        assert result["competency_score"] == 60


class TestEvidenceCoverage:
    def test_full_coverage(self):
        criteria = [
            {"id": "C1", "score": 4, "weight": 0.5, "max_score": 5},
            {"id": "C2", "score": 5, "weight": 0.5, "max_score": 5},
        ]
        cov = compute_evidence_coverage(criteria)
        assert cov == pytest.approx(1.0)

    def test_partial_coverage(self):
        criteria = [
            {"id": "C1", "score": 4, "weight": 0.5, "max_score": 5},
            {"id": "C2", "score": None, "weight": 0.5, "max_score": 5},
        ]
        cov = compute_evidence_coverage(criteria)
        assert cov == pytest.approx(0.5)

    def test_zero_coverage(self):
        criteria = [{"id": "C1", "score": None, "weight": 1.0, "max_score": 5}]
        cov = compute_evidence_coverage(criteria)
        assert cov == 0.0

    def test_required_ids_coverage(self):
        criteria = [
            {"id": "C1", "score": 4, "weight": 0.5, "max_score": 5},
            {"id": "C2", "score": None, "weight": 0.5, "max_score": 5},
        ]
        cov = compute_evidence_coverage(criteria, required_criteria_ids=["C1", "C2"])
        assert cov == pytest.approx(0.5)


class TestCompetencyStatus:
    def test_unassessed(self):
        status = derive_competency_status(0, 0.0)
        assert status == "UNASSESSED"

    def test_in_progress(self):
        status = derive_competency_status(75, 0.5)
        assert status == "IN_PROGRESS"

    def test_evidence_available(self):
        status = derive_competency_status(80, 0.85)
        assert status == "EVIDENCE_AVAILABLE"


class TestCompetencyService:
    def test_score_competency_full(self):
        criteria = [
            {"name": "tool selection", "score": 4, "weight": 0.2, "max_score": 5},
            {"name": "procedure",      "score": 5, "weight": 0.3, "max_score": 5},
            {"name": "execution",      "score": 4, "weight": 0.5, "max_score": 5},
        ]
        result = score_competency("DEMO_NOS_004", criteria, mandatory=True, importance=1.0)
        assert result["nos_id"] == "DEMO_NOS_004"
        assert 70 <= result["competency_score"] <= 100
        assert result["evidence_confidence"] is None  # future module
        assert result["mandatory"] is True
        assert result["status"] in ("UNASSESSED", "IN_PROGRESS", "EVIDENCE_AVAILABLE")

    def test_evidence_confidence_stays_null(self):
        criteria = [{"name": "test", "score": 5, "weight": 1.0, "max_score": 5}]
        result = score_competency("DEMO_NOS_001", criteria)
        assert result["evidence_confidence"] is None

    def test_build_twin_multi_nos(self):
        twin_input = [
            {
                "nos_id": "DEMO_NOS_001",
                "criteria": [{"name": "c1", "score": 4, "weight": 1.0, "max_score": 5}],
                "mandatory": True,
                "importance": 1.0,
            },
            {
                "nos_id": "DEMO_NOS_004",
                "criteria": [{"name": "c1", "score": 5, "weight": 1.0, "max_score": 5}],
                "mandatory": True,
                "importance": 1.0,
            },
        ]
        twin = build_competency_twin("W001", twin_input)
        assert twin["worker_id"] == "W001"
        assert len(twin["competencies"]) == 2
        assert "summary" in twin
        assert twin["summary"]["total_nos"] == 2

    def test_malformed_criteria_rejected_gracefully(self):
        # Criteria with weight=0 — should not crash
        criteria = [{"name": "empty", "score": 5, "weight": 0, "max_score": 5}]
        result = score_competency("DEMO_NOS_001", criteria)
        assert result["competency_score"] == 0
