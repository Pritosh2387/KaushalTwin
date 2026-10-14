"""
KaushalTwin ML Service — Evaluation Metrics Engine
Module 10: Real-World Evaluation, Calibration & Fairness Auditing
Computes Precision, Recall, F1, MRR, Top-k accuracy, and Abstention fidelity.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple


def _tokenize(text: str) -> Set[str]:
    """Lower-case alphanumeric token set for relaxed overlap matching."""
    tokens = re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", text.lower())
    stop_words = {"and", "or", "the", "a", "an", "in", "on", "for", "with", "karta", "hoon", "hai"}
    return {t for t in tokens if len(t) > 1 and t not in stop_words}


def evaluate_skill_extraction(
    extracted_skills: List[str],
    ground_truth_skills: List[str],
    token_overlap_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Evaluate skill extraction quality against expert-annotated skills.

    Computes:
    - Exact match: Precision, Recall, F1
    - Relaxed / token-overlap match: Precision, Recall, F1
    """
    if not extracted_skills and not ground_truth_skills:
        return {
            "exact_precision": 1.0,
            "exact_recall": 1.0,
            "exact_f1": 1.0,
            "relaxed_precision": 1.0,
            "relaxed_recall": 1.0,
            "relaxed_f1": 1.0,
            "extracted_count": 0,
            "ground_truth_count": 0,
        }

    ext_norm = [s.strip().lower() for s in extracted_skills if s.strip()]
    gt_norm = [s.strip().lower() for s in ground_truth_skills if s.strip()]

    # 1. Exact Matching
    exact_matches = 0
    matched_gt_indices: Set[int] = set()

    for ext in ext_norm:
        for idx, gt in enumerate(gt_norm):
            if idx not in matched_gt_indices and ext == gt:
                exact_matches += 1
                matched_gt_indices.add(idx)
                break

    exact_prec = exact_matches / len(ext_norm) if ext_norm else 0.0
    exact_rec = exact_matches / len(gt_norm) if gt_norm else 0.0
    exact_f1 = (2 * exact_prec * exact_rec / (exact_prec + exact_rec)) if (exact_prec + exact_rec) > 0 else 0.0

    # 2. Relaxed Token Overlap Matching (Jaccard similarity >= threshold)
    relaxed_matches = 0
    matched_gt_relaxed: Set[int] = set()

    for ext in ext_norm:
        ext_tokens = _tokenize(ext)
        best_jaccard = 0.0
        best_idx = -1

        for idx, gt in enumerate(gt_norm):
            if idx not in matched_gt_relaxed:
                gt_tokens = _tokenize(gt)
                intersection = ext_tokens & gt_tokens
                union = ext_tokens | gt_tokens
                jaccard = len(intersection) / len(union) if union else 0.0
                if jaccard > best_jaccard:
                    best_jaccard = jaccard
                    best_idx = idx

        if best_jaccard >= token_overlap_threshold and best_idx >= 0:
            relaxed_matches += 1
            matched_gt_relaxed.add(best_idx)

    relaxed_prec = relaxed_matches / len(ext_norm) if ext_norm else 0.0
    relaxed_rec = relaxed_matches / len(gt_norm) if gt_norm else 0.0
    relaxed_f1 = (2 * relaxed_prec * relaxed_rec / (relaxed_prec + relaxed_rec)) if (relaxed_prec + relaxed_rec) > 0 else 0.0

    return {
        "exact_precision": round(exact_prec, 4),
        "exact_recall": round(exact_rec, 4),
        "exact_f1": round(exact_f1, 4),
        "relaxed_precision": round(relaxed_prec, 4),
        "relaxed_recall": round(relaxed_rec, 4),
        "relaxed_f1": round(relaxed_f1, 4),
        "extracted_count": len(ext_norm),
        "ground_truth_count": len(gt_norm),
    }


def evaluate_nos_mapping(
    predicted_candidates: List[Dict[str, Any]],
    ground_truth_ids: List[str],
    acceptable_alternatives: Optional[List[str]] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Evaluate NOS candidate ranking against expert targets and acceptable alternatives.

    Computes:
    - top_1_accuracy: 1.0 if top-1 predicted candidate matches target or alternative
    - top_k_accuracy: 1.0 if any candidate in top-k matches target or alternative
    - reciprocal_rank: 1 / rank of first match, or 0.0 if not found
    """
    all_valid_targets = set(ground_truth_ids) | set(acceptable_alternatives or [])

    if not all_valid_targets:
        return {
            "top_1_accuracy": 0.0,
            "top_k_accuracy": 0.0,
            "reciprocal_rank": 0.0,
            "match_found": False,
            "match_rank": None,
            "matched_id": None,
        }

    cand_ids = [
        str(c.get("nos_id") or c.get("id") or c.get("code") or "").strip()
        for c in predicted_candidates
    ]

    top_1_match = False
    top_k_match = False
    reciprocal_rank = 0.0
    matched_id = None
    match_rank = None

    for rank, cand_id in enumerate(cand_ids[:top_k], start=1):
        if cand_id in all_valid_targets:
            if rank == 1:
                top_1_match = True
            top_k_match = True
            reciprocal_rank = 1.0 / rank
            matched_id = cand_id
            match_rank = rank
            break

    return {
        "top_1_accuracy": 1.0 if top_1_match else 0.0,
        "top_k_accuracy": 1.0 if top_k_match else 0.0,
        "reciprocal_rank": round(reciprocal_rank, 4),
        "match_found": top_k_match,
        "match_rank": match_rank,
        "matched_id": matched_id,
    }


def evaluate_abstention(
    predicted_abstained: bool,
    ground_truth_should_abstain: bool,
) -> Dict[str, Any]:
    """
    Evaluate whether the model correctly abstained or appropriately attempted prediction.

    Categories:
    - TRUE_ABSTAIN: Correctly abstained when information was out-of-domain or insufficient.
    - TRUE_PREDICT: Correctly predicted when valid trade information was present.
    - FALSE_ABSTAIN: Erroneously abstained on valid trade information (False Negative).
    - FALSE_PREDICT: Erroneously attempted prediction on out-of-domain content (Unsafe False Positive).
    """
    if predicted_abstained and ground_truth_should_abstain:
        category = "TRUE_ABSTAIN"
        is_correct = True
    elif not predicted_abstained and not ground_truth_should_abstain:
        category = "TRUE_PREDICT"
        is_correct = True
    elif predicted_abstained and not ground_truth_should_abstain:
        category = "FALSE_ABSTAIN"
        is_correct = False
    else:
        category = "FALSE_PREDICT"
        is_correct = False

    return {
        "is_correct": is_correct,
        "category": category,
        "predicted_abstained": predicted_abstained,
        "ground_truth_should_abstain": ground_truth_should_abstain,
    }


def aggregate_abstention_metrics(
    evaluations: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Aggregate a list of individual abstention evaluations into precision, recall, and FAR."""
    if not evaluations:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "false_abstention_rate": 0.0,
            "unsafe_prediction_rate": 0.0,
        }

    ta = sum(1 for e in evaluations if e["category"] == "TRUE_ABSTAIN")
    tp = sum(1 for e in evaluations if e["category"] == "TRUE_PREDICT")
    fa = sum(1 for e in evaluations if e["category"] == "FALSE_ABSTAIN")
    fp = sum(1 for e in evaluations if e["category"] == "FALSE_PREDICT")
    total = len(evaluations)

    accuracy = (ta + tp) / total if total > 0 else 0.0
    precision = ta / (ta + fp) if (ta + fp) > 0 else 0.0
    recall = ta / (ta + fa) if (ta + fa) > 0 else 0.0
    far = fa / (tp + fa) if (tp + fa) > 0 else 0.0
    unsafe_rate = fp / (ta + fp) if (ta + fp) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_abstention_rate": round(far, 4),
        "unsafe_prediction_rate": round(unsafe_rate, 4),
        "true_abstain": ta,
        "true_predict": tp,
        "false_abstain": fa,
        "false_predict": fp,
    }
