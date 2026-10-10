"""
KaushalTwin ML Service — Service: Skill Gap + Evidence Debt (Module 6)
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from ml.algorithms.skill_gap import analyze_skill_gaps, NOSGapAnalysis


class SkillGapService:
    """Service for calculating skill gaps and evidence debt."""

    @staticmethod
    def analyze_skill_gaps(
        worker_id: str,
        competencies: List[Dict[str, Any]],
        evidence_records: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps and evidence debt for a worker.

        Args:
            worker_id: Worker identifier
            competencies: List of competency dictionaries
            evidence_records: List of evidence records (optional)

        Returns:
            Dictionary with skill gap analysis results
        """
        return analyze_skill_gaps(worker_id, competencies, evidence_records)

    @staticmethod
    def calculate_evidence_debt(evidence_coverage: float) -> float:
        """
        Calculate evidence debt from evidence coverage.

        Args:
            evidence_coverage: Evidence coverage ratio (0.0-1.0)

        Returns:
            Evidence debt (1.0 - evidence_coverage)
        """
        return max(0.0, min(1.0, 1.0 - evidence_coverage))

    @staticmethod
    def get_gap_summary(gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of skill gaps.

        Args:
            gaps: List of gap analysis dictionaries

        Returns:
            Summary dictionary
        """
        if not gaps:
            return {
                "total_gaps": 0,
                "mandatory_gaps": 0,
                "critical_gaps": 0,
                "average_evidence_debt": 0.0,
            }

        mandatory_gaps = len([g for g in gaps if g.get("mandatory", False)])
        # Critical gaps: mandatory NOS with high evidence debt
        critical_gaps = len([
            g for g in gaps
            if g.get("mandatory", False) and g.get("evidence_debt", 0) > 0.5
        ])
        avg_debt = sum(g.get("evidence_debt", 0) for g in gaps) / len(gaps)

        return {
            "total_gaps": len(gaps),
            "mandatory_gaps": mandatory_gaps,
            "critical_gaps": critical_gaps,
            "average_evidence_debt": avg_debt,
            "gaps_by_status": {
                "STRONG": len([g for g in gaps if g.get("status") == "STRONG"]),
                "WEAK": len([g for g in gaps if g.get("status") == "WEAK"]),
                "MISSING": len([g for g in gaps if g.get("status") == "MISSING"]),
            }
        }