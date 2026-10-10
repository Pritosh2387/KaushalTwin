"""
Unit Tests — Module 8: Assessor Calibration + Consistency
"""
import pytest
from ml.algorithms.calibration import (
    calculate_assessor_calibration,
    AssessorProfile,
    CalibrationResult,
)
from ml.services.calibration_service import CalibrationService


class TestCalibrationAlgorithm:
    def test_calculate_assessor_calibration_consistent(self):
        """Test calibration with consistent assessors."""
        assessor_scores = [
            # Assessor A01 - consistent scores around 75
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 76},
            {"assessor_id": "A01", "worker_id": "W002", "competency_area": "safety", "score": 74},
            {"assessor_id": "A01", "worker_id": "W003", "competency_area": "safety", "score": 75},

            # Assessor A02 - consistent scores around 76
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": 77},
            {"assessor_id": "A02", "worker_id": "W002", "competency_area": "safety", "score": 75},
            {"assessor_id": "A02", "worker_id": "W003", "competency_area": "safety", "score": 76},
        ]

        result = calculate_assessor_calibration(assessor_scores)

        assert isinstance(result, CalibrationResult)
        assert len(result.assessor_profiles) == 2

        # Check that both assessors have similar means
        a01_profile = next(p for p in result.assessor_profiles if p.assessor_id == "A01")
        a02_profile = next(p for p in result.assessor_profiles if p.assessor_id == "A02")

        assert abs(a01_profile.mean_score - 75) < 1.0
        assert abs(a02_profile.mean_score - 76) < 1.0
        assert abs(a01_profile.severity_delta) < 1.0  # Close to group mean
        assert abs(a02_profile.severity_delta) < 1.0  # Close to group mean

        # Should have good agreement
        overall_agreement = result.agreement_metrics.get("overall_percentage_agreement")
        assert overall_agreement is not None
        assert overall_agreement >= 60  # At least moderate agreement

    def test_calculate_assessor_calibration_inconsistent(self):
        """Test calibration with inconsistent assessors."""
        assessor_scores = [
            # Assessor A01 - lenient (high scores)
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 90},
            {"assessor_id": "A01", "worker_id": "W002", "competency_area": "safety", "score": 92},
            {"assessor_id": "A01", "worker_id": "W003", "competency_area": "safety", "score": 88},

            # Assessor A02 - strict (low scores)
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": 50},
            {"assessor_id": "A02", "worker_id": "W002", "competency_area": "safety", "score": 48},
            {"assessor_id": "A02", "worker_id": "W003", "competency_area": "safety", "score": 52},
        ]

        result = calculate_assessor_calibration(assessor_scores)

        assert len(result.assessor_profiles) == 2

        # Check that assessors have opposite severity deltas
        a01_profile = next(p for p in result.assessor_profiles if p.assessor_id == "A01")
        a02_profile = next(p for p in result.assessor_profiles if p.assessor_id == "A02")

        # A01 should be lenient (positive delta), A02 should be strict (negative delta)
        assert a01_profile.severity_delta > 10  # Significantly lenient
        assert a02_profile.severity_delta < -10  # Significantly strict

        # Should have low agreement
        overall_agreement = result.agreement_metrics.get("overall_percentage_agreement")
        assert overall_agreement is not None
        assert overall_agreement < 40  # Poor agreement

    def test_calculate_assessor_calibration_single_assessor(self):
        """Test calibration with single assessor."""
        assessor_scores = [
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 75},
            {"assessor_id": "A01", "worker_id": "W002", "competency_area": "safety", "score": 80},
            {"assessor_id": "A01", "worker_id": "W003", "competency_area": "safety", "score": 70},
        ]

        result = calculate_assessor_calibration(assessor_scores)

        assert len(result.assessor_profiles) == 1
        profile = result.assessor_profiles[0]
        assert profile.assessor_id == "A01"
        assert profile.mean_score == 75.0  # (75+80+70)/3
        # With only one assessor, group mean should equal assessor mean
        assert profile.group_mean == 75.0
        assert profile.severity_delta == 0.0

    def test_calculate_assessor_calibration_multiple_competencies(self):
        """Test calibration across multiple competency areas."""
        assessor_scores = [
            # Assessor A01 scores
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 80},
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "installation", "score": 70},
            {"assessor_id": "A01", "worker_id": "W002", "competency_area": "safety", "score": 82},
            {"assessor_id": "A01", "worker_id": "W002", "competency_area": "installation", "score": 72},

            # Assessor A02 scores
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": 85},
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "installation", "score": 65},
            {"assessor_id": "A02", "worker_id": "W002", "competency_area": "safety", "score": 87},
            {"assessor_id": "A02", "worker_id": "W002", "competency_area": "installation", "score": 68},
        ]

        result = calculate_assessor_calibration(
            assessor_scores=assessor_scores,
            competency_areas=["safety", "installation"]
        )

        assert len(result.assessor_profiles) == 2
        # Should have metrics for both competency areas
        area_metrics = result.agreement_metrics.get("area_metrics", {})
        assert "safety" in area_metrics
        assert "installation" in area_metrics

        # Each area should have assessor data
        assert area_metrics["safety"]["assessors_with_data"] == 2
        assert area_metrics["installation"]["assessors_with_data"] == 2

    def test_calibration_service_integration(self):
        """Test service layer integration."""
        assessor_scores = [
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 75},
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": 80},
        ]

        # Test main service method
        result = CalibrationService.calculate_assessor_calibration(assessor_scores)

        assert "assessor_profiles" in result
        assert "agreement_metrics" in result
        assert "disagreement_areas" in result
        assert "overall_consistency" in result
        assert "recommended_actions" in result

        assert len(result["assessor_profiles"]) == 2
        assert result["assessor_profiles"][0]["assessor_id"] == "A01"
        assert result["assessor_profiles"][1]["assessor_id"] == "A02"

        # Test single assessor profile service
        profile = CalibrationService.get_assessor_profile(assessor_scores, "A01")
        assert profile is not None
        assert profile["assessor_id"] == "A01"
        assert profile["mean_score"] == 75.0

        # Test assessor agreement service
        agreement_result = CalibrationService.calculate_agreement_between_assessors(
            [{"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 75}],
            [{"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": 80}]
        )
        assert "assessor_profiles" in agreement_result
        assert len(agreement_result["assessor_profiles"]) == 2

    def test_calibration_edge_cases(self):
        """Test edge cases."""
        # Empty assessor scores
        result = calculate_assessor_calibration([])
        assert len(result.assessor_profiles) == 0
        assert result.overall_consistency == "NO_DATA"

        # Assessor scores with missing data
        assessor_scores_incomplete = [
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety"},  # Missing score
            {"assessor_id": "A02", "worker_id": "W001", "competency_area": "safety", "score": "invalid"},  # Invalid score
            {"assessor_id": "A03", "worker_id": "W001", "competency_area": "safety", "score": 75},  # Valid
        ]

        result = calculate_assessor_calibration(assessor_scores_incomplete)
        # Should only process the valid score
        assert len(result.assessor_profiles) == 1
        assert result.assessor_profiles[0].assessor_id == "A03"

        # Single assessment
        result = calculate_assessor_calibration([
            {"assessor_id": "A01", "worker_id": "W001", "competency_area": "safety", "score": 75}
        ])
        assert len(result.assessor_profiles) == 1
        assert result.assessor_profiles[0].total_assessments == 1