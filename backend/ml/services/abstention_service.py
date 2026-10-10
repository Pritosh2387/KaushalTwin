"""
KaushalTwin ML Service — Service: Abstention / Evidence Sufficiency Engine (Module 7)
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from ml.algorithms.abstention import check_evidence_sufficiency, should_abstain


class AbstentionService:
    """Service for evidence sufficiency and abstention decisions."""

    @staticmethod
    def check_evidence_sufficiency(
        worker_id: str,
        competencies: List[Dict[str, Any]],
        evidence_records: Optional[List[Dict[str, Any]]] = None,
        assessment_task_results: Optional[List[Dict[str, Any]]] = None,
        assessor_observations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if evidence is sufficient to proceed with assessment.

        Args:
            worker_id: Worker identifier
            competencies: List of competency dictionaries
            evidence_records: List of evidence records (optional)
            assessment_task_results: Results from completed assessment tasks (optional)
            assessor_observations: Direct observations by assessors (optional)

        Returns:
            Dictionary with abstention decision
        """
        decision = check_evidence_sufficiency(
            worker_id=worker_id,
            competencies=competencies,
            evidence_records=evidence_records,
            assessment_task_results=assessment_task_results,
            assessor_observations=assessor_observations,
        )
        # Convert dataclass to dict for JSON serialization
        return {
            "status": decision.status,
            "confidence": decision.confidence,
            "reason_codes": decision.reason_codes,
            "reasons": decision.reasons,
            "recommended_action": decision.recommended_action,
            "next_task_id": decision.next_task_id,
            "metadata": decision.metadata,
        }

    @staticmethod
    def should_abstain(
        competencies: List[Dict[str, Any]],
        threshold_evidence_coverage: float = 0.4,
        threshold_evidence_confidence: float = 0.4,
    ) -> Dict[str, Any]:
        """
        Determine if abstention is warranted based on simple thresholds.

        Args:
            competencies: List of competency dictionaries
            threshold_evidence_coverage: Minimum acceptable evidence coverage
            threshold_evidence_confidence: Minimum acceptable evidence confidence

        Returns:
            Dictionary with abstention recommendation
        """
        should_abstain_flag, reasons = should_abstain(
            competencies=competencies,
            threshold_evidence_coverage=threshold_evidence_coverage,
            threshold_evidence_confidence=threshold_evidence_confidence,
        )

        return {
            "should_abstain": should_abstain_flag,
            "reason": "; ".join(reasons) if reasons else "Sufficient evidence for assessment",
            "reasons": reasons,
        }

    @staticmethod
    def get_abstention_reasons(
        competencies: List[Dict[str, Any]],
        evidence_records: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Get human-readable reasons for potential abstention.

        Args:
            competencies: List of competency dictionaries
            evidence_records: List of evidence records (optional)

        Returns:
            List of reason strings
        """
        # Reuse the core logic but extract just the reasons
        decision = check_evidence_sufficiency(
            worker_id="temp",
            competencies=competencies,
            evidence_records=evidence_records or [],
        )
        return decision["reasons"]