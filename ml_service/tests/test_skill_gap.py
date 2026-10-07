"""
Unit Tests — Module 6: Skill Gap + Evidence Debt
"""
import pytest
from app.algorithms.skill_gap import (
    calculate_skill_gap,
    analyze_skill_gaps,
    NOSGapAnalysis,
)
from app.services.skill_gap_service import SkillGapService


class TestSkillGapAlgorithm:
    def test_calculate_skill_gap_strong(self):
        """Test strong competency with strong evidence."""
        gap = calculate_skill_gap(
            nos_id="DEMO_NOS_004",
            competency_score=85,
            evidence_confidence=0.9,
            evidence_coverage=0.85,
            mandatory=True,
        )
        assert gap.competency_score == 85
        assert gap.evidence_confidence == 0.9
        assert gap.evidence_coverage == 0.85
        assert gap.evidence_debt == pytest.approx(0.15, rel=1e-2)
        assert gap.status == "STRONG"
        assert gap.mandatory == True

    def test_calculate_skill_gap_weak(self):
        """Test moderate competency with some evidence gaps."""
        gap = calculate_skill_gap(
            nos_id="DEMO_NOS_005",
            competency_score=65,
            evidence_confidence=0.5,
            evidence_coverage=0.55,
            mandatory=False,
        )
        assert gap.competency_score == 65
        assert gap.evidence_confidence == 0.5
        assert gap.evidence_coverage == 0.55
        assert gap.evidence_debt == pytest.approx(0.45, rel=1e-2)
        assert gap.status == "WEAK"

    def test_calculate_skill_gap_missing(self):
        """Test low competency or insufficient evidence."""
        gap = calculate_skill_gap(
            nos_id="DEMO_NOS_006",
            competency_score=40,
            evidence_confidence=0.3,
            evidence_coverage=0.2,
            mandatory=True,
        )
        assert gap.competency_score == 40
        assert gap.evidence_confidence == 0.3
        assert gap.evidence_coverage == 0.2
        assert gap.evidence_debt == 0.8
        assert gap.status == "MISSING"

    def test_calculate_skill_gap_mandatory_low_evidence(self):
        """Test mandatory NOS with low evidence coverage."""
        gap = calculate_skill_gap(
            nos_id="DEMO_NOS_007",
            competency_score=70,
            evidence_confidence=0.6,
            evidence_coverage=0.3,  # Low coverage
            mandatory=True,
        )
        # Should be MISSING due to mandatory + low evidence
        assert gap.status == "MISSING"
        assert "Mandatory NOS" in gap.reason

    def test_analyze_skill_gaps_empty(self):
        """Test analysis with empty competencies."""
        result = analyze_skill_gaps(
            worker_id="W001",
            competencies=[],
        )
        assert result["worker_id"] == "W001"
        assert result["overall_evidence_coverage"] == 0.0
        assert result["overall_evidence_debt"] == 1.0
        assert result["gaps"] == []

    def test_analyze_skill_gaps_single(self):
        """Test analysis with single competency."""
        competencies = [{
            "nos_id": "DEMO_NOS_004",
            "competency_score": 80,
            "evidence_confidence": 0.8,
            "evidence_coverage": 0.75,
            "mandatory": True,
        }]

        result = analyze_skill_gaps(
            worker_id="W001",
            competencies=competencies,
        )

        assert result["worker_id"] == "W001"
        assert result["overall_evidence_coverage"] == 0.75
        assert result["overall_evidence_debt"] == 0.25
        assert len(result["gaps"]) == 1

        gap = result["gaps"][0]
        assert gap["nos_id"] == "DEMO_NOS_004"
        assert gap["competency_score"] == 80
        assert gap["evidence_confidence"] == 0.8
        assert gap["evidence_coverage"] == 0.75
        assert gap["evidence_debt"] == 0.25

    def test_skill_gap_service_calculate_evidence_debt(self):
        """Test service method for calculating evidence debt."""
        assert SkillGapService.calculate_evidence_debt(0.0) == 1.0
        assert SkillGapService.calculate_evidence_debt(0.5) == 0.5
        assert SkillGapService.calculate_evidence_debt(1.0) == 0.0
        assert SkillGapService.calculate_evidence_debt(0.8) == pytest.approx(0.2, rel=1e-2)

    def test_skill_gap_service_get_gap_summary(self):
        """Test service method for gap summary."""
        gaps = [
            {
                "nos_id": "DEMO_NOS_001",
                "mandatory": True,
                "evidence_debt": 0.2,
                "status": "STRONG",
            },
            {
                "nos_id": "DEMO_NOS_002",
                "mandatory": True,
                "evidence_debt": 0.6,
                "status": "MISSING",
            },
            {
                "nos_id": "DEMO_NOS_003",
                "mandatory": False,
                "evidence_debt": 0.3,
                "status": "WEAK",
            },
        ]

        summary = SkillGapService.get_gap_summary(gaps)
        assert summary["total_gaps"] == 3
        assert summary["mandatory_gaps"] == 2
        assert summary["critical_gaps"] == 1  # One mandatory with debt > 0.5
        assert summary["average_evidence_debt"] == pytest.approx(0.366, rel=1e-2)
        assert summary["gaps_by_status"]["STRONG"] == 1
        assert summary["gaps_by_status"]["WEAK"] == 1
        assert summary["gaps_by_status"]["MISSING"] == 1