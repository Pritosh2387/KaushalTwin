"""
KaushalTwin ML Service — Fairness & Disparity Auditing Engine
Module 10: Real-World Evaluation, Calibration & Fairness Auditing

Performs disaggregated evaluations across:
- Trades: electrician, plumber, welder, mason, general
- Language styles: formal, colloquial, hinglish / code_switched, terse

Computes:
- Trade Parity Ratio (Four-Fifths Rule compliance: min_f1 / max_f1 >= 0.80)
- Max Accuracy Disparity: max - min across trade cohorts
- False Abstention Disparity: max(FAR) - min(FAR) across language styles
- Structured Fairness Verdict and bias mitigation recommendations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from ml.evaluation.metrics import aggregate_abstention_metrics


def audit_fairness_slices(
    evaluated_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Audit model performance across trade and language style demographic slices.

    Each record in evaluated_records should contain:
    - trade: str
    - style: str
    - extraction_f1: float (relaxed or exact)
    - mapping_top1: float (1.0 or 0.0)
    - mapping_mrr: float
    - abstention_eval: Dict[str, Any] (from evaluate_abstention)
    """
    if not evaluated_records:
        return {
            "verdict": "NO_DATA",
            "trade_parity_ratio": 1.0,
            "max_trade_disparity": 0.0,
            "max_style_disparity": 0.0,
            "false_abstention_disparity": 0.0,
            "trade_slices": {},
            "style_slices": {},
            "recommendations": ["No evaluation records provided for fairness audit."],
        }

    # Group by Trade
    trade_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in evaluated_records:
        t = str(r.get("trade", "general")).lower().strip()
        trade_groups.setdefault(t, []).append(r)

    # Group by Style
    style_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in evaluated_records:
        s = str(r.get("style", "standard")).lower().strip()
        style_groups.setdefault(s, []).append(r)

    def _summarize_slice(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        count = len(records)
        f1_vals = [r.get("extraction_f1", 0.0) for r in records]
        top1_vals = [r.get("mapping_top1", 0.0) for r in records]
        mrr_vals = [r.get("mapping_mrr", 0.0) for r in records]
        abst_evals = [r.get("abstention_eval", {}) for r in records if "abstention_eval" in r]

        avg_f1 = float(np.mean(f1_vals)) if f1_vals else 0.0
        avg_top1 = float(np.mean(top1_vals)) if top1_vals else 0.0
        avg_mrr = float(np.mean(mrr_vals)) if mrr_vals else 0.0

        abst_summary = aggregate_abstention_metrics(abst_evals) if abst_evals else {
            "false_abstention_rate": 0.0,
            "unsafe_prediction_rate": 0.0,
        }

        return {
            "sample_count": count,
            "mean_extraction_f1": round(avg_f1, 4),
            "mean_mapping_top1": round(avg_top1, 4),
            "mean_mapping_mrr": round(avg_mrr, 4),
            "false_abstention_rate": abst_summary.get("false_abstention_rate", 0.0),
            "unsafe_prediction_rate": abst_summary.get("unsafe_prediction_rate", 0.0),
        }

    trade_slices = {t: _summarize_slice(recs) for t, recs in trade_groups.items()}
    style_slices = {s: _summarize_slice(recs) for s, recs in style_groups.items()}

    # Compute Trade Disparities
    trade_f1s = [ts["mean_extraction_f1"] for ts in trade_slices.values() if ts["sample_count"] > 0]
    trade_top1s = [ts["mean_mapping_top1"] for ts in trade_slices.values() if ts["sample_count"] > 0]

    min_trade_f1 = min(trade_f1s) if trade_f1s else 0.0
    max_trade_f1 = max(trade_f1s) if trade_f1s else 0.0
    trade_parity_ratio = (min_trade_f1 / max_trade_f1) if max_trade_f1 > 1e-6 else 1.0

    min_trade_top1 = min(trade_top1s) if trade_top1s else 0.0
    max_trade_top1 = max(trade_top1s) if trade_top1s else 0.0
    max_trade_disparity = max_trade_top1 - min_trade_top1

    # Compute Style Disparities
    style_f1s = [ss["mean_extraction_f1"] for ss in style_slices.values() if ss["sample_count"] > 0]
    min_style_f1 = min(style_f1s) if style_f1s else 0.0
    max_style_f1 = max(style_f1s) if style_f1s else 0.0
    max_style_disparity = max_style_f1 - min_style_f1

    # False Abstention Disparities across styles (check if colloquial/Hinglish suffer higher rejection)
    style_fars = [ss["false_abstention_rate"] for ss in style_slices.values() if ss["sample_count"] > 0]
    far_disparity = (max(style_fars) - min(style_fars)) if style_fars else 0.0

    # Determine Verdict
    # Four-Fifths Rule (80% rule): Parity ratio >= 0.80
    recommendations: List[str] = []

    if trade_parity_ratio >= 0.80 and max_trade_disparity <= 0.15 and far_disparity <= 0.15:
        verdict = "FAIR"
        recommendations.append("System satisfies the 80% trade parity threshold and exhibits uniform abstention.")
    elif trade_parity_ratio >= 0.65 and max_trade_disparity <= 0.25 and far_disparity <= 0.25:
        verdict = "MODERATE_DISPARITY"
        recommendations.append(
            f"Trade parity ratio ({trade_parity_ratio:.2f}) falls below 0.80 threshold. "
            "Consider enriching keyword dictionaries and qualification standards for lower-performing trades."
        )
    else:
        verdict = "SIGNIFICANT_DISPARITY"
        recommendations.append(
            f"Significant disparity detected (parity ratio: {trade_parity_ratio:.2f}, FAR disparity: {far_disparity:.2f}). "
            "Model requires re-weighting or domain-specific calibration before deployment."
        )

    # Style-specific bias warning
    for s_name, s_data in style_slices.items():
        if s_data["false_abstention_rate"] > 0.30:
            recommendations.append(
                f"Elevated False Abstention Rate ({s_data['false_abstention_rate']:.2f}) in '{s_name}' style transcripts. "
                "Workers using this style may experience unwarranted assessment deferral."
            )

    return {
        "verdict": verdict,
        "trade_parity_ratio": round(trade_parity_ratio, 4),
        "max_trade_disparity": round(max_trade_disparity, 4),
        "max_style_disparity": round(max_style_disparity, 4),
        "false_abstention_disparity": round(far_disparity, 4),
        "trade_slices": trade_slices,
        "style_slices": style_slices,
        "recommendations": recommendations,
        "assessor_notice": (
            "Disparity metrics assist in auditing algorithm equity. "
            "Human assessors must ensure equal opportunity regardless of candidate language dialect or trade."
        ),
    }
