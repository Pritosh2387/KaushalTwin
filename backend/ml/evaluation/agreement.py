"""
KaushalTwin ML Service — Assessor Agreement & Inter-Rater Reliability Engine
Module 10: Real-World Evaluation, Calibration & Fairness Auditing

Computes:
1. Cohen's Kappa (chance-corrected pairwise nominal agreement)
2. Weighted Kappa (linear and quadratic for ordinal competency ratings)
3. Fleiss' Kappa (generalized multi-assessor nominal agreement)
4. Krippendorff's Alpha (nominal and interval, handling missing ratings)
5. AI-Assessor Alignment (evaluating AI prediction bias against human expert consensus)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import numpy as np


def cohen_kappa_interpretation(kappa: float) -> str:
    """Return Landis & Koch (1977) benchmark interpretation of Kappa values."""
    if kappa < 0.0:
        return "Poor (Less than chance)"
    elif kappa <= 0.20:
        return "Slight Agreement"
    elif kappa <= 0.40:
        return "Fair Agreement"
    elif kappa <= 0.60:
        return "Moderate Agreement"
    elif kappa <= 0.80:
        return "Substantial Agreement"
    else:
        return "Almost Perfect Agreement"


def compute_cohen_kappa(
    rater1: Sequence[Any],
    rater2: Sequence[Any],
) -> Dict[str, Any]:
    """
    Compute Cohen's Kappa for two raters on nominal categories.
    kappa = (P_o - P_e) / (1 - P_e)
    """
    if len(rater1) != len(rater2):
        raise ValueError(f"Rater sequences must have equal length, got {len(rater1)} and {len(rater2)}")
    if len(rater1) == 0:
        return {
            "kappa": 1.0,
            "observed_agreement": 1.0,
            "expected_agreement": 1.0,
            "sample_size": 0,
            "interpretation": "Almost Perfect Agreement",
        }

    categories = sorted(list(set(rater1) | set(rater2)))
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    n_cats = len(categories)
    N = len(rater1)

    conf_matrix = np.zeros((n_cats, n_cats), dtype=np.int64)
    for r1, r2 in zip(rater1, rater2):
        conf_matrix[cat_to_idx[r1], cat_to_idx[r2]] += 1

    # Observed agreement
    p_o = float(np.trace(conf_matrix)) / N

    # Expected agreement by chance
    sum_row = np.sum(conf_matrix, axis=1) / float(N)
    sum_col = np.sum(conf_matrix, axis=0) / float(N)
    p_e = float(np.sum(sum_row * sum_col))

    if abs(1.0 - p_e) < 1e-9:
        kappa = 1.0 if abs(p_o - 1.0) < 1e-9 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    # Bound kappa to [-1.0, 1.0]
    kappa = max(-1.0, min(1.0, kappa))

    return {
        "kappa": round(float(kappa), 4),
        "observed_agreement": round(float(p_o), 4),
        "expected_agreement": round(float(p_e), 4),
        "sample_size": N,
        "categories": [str(c) for c in categories],
        "interpretation": cohen_kappa_interpretation(kappa),
    }


def compute_weighted_kappa(
    rater1: Sequence[int],
    rater2: Sequence[int],
    weights: str = "quadratic",
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute Weighted Cohen's Kappa for ordinal competency ratings.
    Weights: 'linear' or 'quadratic'.
    """
    if len(rater1) != len(rater2):
        raise ValueError("Rater sequences must have equal length")
    if len(rater1) == 0:
        return {
            "weighted_kappa": 1.0,
            "weighting_type": weights,
            "sample_size": 0,
            "interpretation": "Almost Perfect Agreement",
        }

    all_vals = list(rater1) + list(rater2)
    low = min_rating if min_rating is not None else min(all_vals)
    high = max_rating if max_rating is not None else max(all_vals)

    if low == high:
        return {
            "weighted_kappa": 1.0,
            "observed_weighted": 1.0,
            "expected_weighted": 1.0,
            "sample_size": len(rater1),
            "weighting_type": weights,
            "interpretation": "Almost Perfect Agreement",
        }

    num_levels = high - low + 1
    conf_matrix = np.zeros((num_levels, num_levels), dtype=np.float64)
    for r1, r2 in zip(rater1, rater2):
        conf_matrix[r1 - low, r2 - low] += 1

    N = float(len(rater1))

    # Construct weight matrix
    weight_mat = np.zeros((num_levels, num_levels), dtype=np.float64)
    for i in range(num_levels):
        for j in range(num_levels):
            diff = abs(i - j)
            if weights == "linear":
                weight_mat[i, j] = 1.0 - (diff / (num_levels - 1))
            else:  # quadratic
                weight_mat[i, j] = 1.0 - ((diff ** 2) / ((num_levels - 1) ** 2))

    p_o = float(np.sum(weight_mat * conf_matrix) / N)

    row_sum = np.sum(conf_matrix, axis=1)
    col_sum = np.sum(conf_matrix, axis=0)
    expected_matrix = np.outer(row_sum, col_sum) / N
    p_e = float(np.sum(weight_mat * expected_matrix) / N)

    if abs(1.0 - p_e) < 1e-9:
        kappa = 1.0 if abs(p_o - 1.0) < 1e-9 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    kappa = max(-1.0, min(1.0, kappa))

    return {
        "weighted_kappa": round(float(kappa), 4),
        "observed_weighted": round(float(p_o), 4),
        "expected_weighted": round(float(p_e), 4),
        "weighting_type": weights,
        "sample_size": int(N),
        "rating_range": [low, high],
        "interpretation": cohen_kappa_interpretation(kappa),
    }


def compute_fleiss_kappa(
    ratings_matrix: Sequence[Sequence[int]],
) -> Dict[str, Any]:
    """
    Compute Fleiss' Kappa for multi-assessor nominal categories.
    ratings_matrix[i][j] = number of raters assigning subject i to category j.
    Each row i must sum to m (number of raters).
    """
    mat = np.array(ratings_matrix, dtype=np.int64)
    if mat.ndim != 2 or mat.shape[0] == 0:
        return {"fleiss_kappa": 1.0, "interpretation": "Almost Perfect Agreement", "sample_size": 0}

    N, k = mat.shape
    row_sums = np.sum(mat, axis=1)
    m = row_sums[0]

    # Verify all subjects have m raters
    if not np.all(row_sums == m):
        raise ValueError("Each subject must be rated by the same number of raters (m).")
    if m <= 1:
        return {"fleiss_kappa": 1.0, "interpretation": "Insufficient raters per subject", "sample_size": N}

    # Proportion of assignments to category j
    p_j = np.sum(mat, axis=0) / float(N * m)

    # Subject agreement P_i
    P_i = (np.sum(mat ** 2, axis=1) - m) / float(m * (m - 1))
    p_bar = float(np.mean(P_i))

    # Expected agreement by chance
    p_bar_e = float(np.sum(p_j ** 2))

    if abs(1.0 - p_bar_e) < 1e-9:
        kappa = 1.0 if abs(p_bar - 1.0) < 1e-9 else 0.0
    else:
        kappa = (p_bar - p_bar_e) / (1.0 - p_bar_e)

    kappa = max(-1.0, min(1.0, kappa))

    return {
        "fleiss_kappa": round(float(kappa), 4),
        "mean_observed": round(float(p_bar), 4),
        "mean_expected": round(float(p_bar_e), 4),
        "subjects": N,
        "raters_per_subject": int(m),
        "categories_count": k,
        "interpretation": cohen_kappa_interpretation(kappa),
    }


def compute_krippendorff_alpha(
    reliability_data: Sequence[Sequence[Optional[Union[int, float, str]]]],
    level_of_measurement: str = "nominal",
) -> Dict[str, Any]:
    """
    Compute Krippendorff's Alpha for inter-coder reliability.
    reliability_data: matrix where rows are coders/raters and columns are units/subjects.
    None represents missing data.
    Supported levels: 'nominal', 'interval'.
    """
    data = list(reliability_data)
    if not data or len(data) == 0:
        return {"alpha": 1.0, "interpretation": "Almost Perfect Agreement"}

    n_raters = len(data)
    n_units = len(data[0])

    # Collect pairs of ratings on the same unit
    pairs: List[Tuple[Any, Any]] = []
    unit_valid_counts = []

    for u in range(n_units):
        ratings_u = [data[r][u] for r in range(n_raters) if data[r][u] is not None]
        m_u = len(ratings_u)
        unit_valid_counts.append(m_u)
        if m_u >= 2:
            for i in range(m_u):
                for j in range(m_u):
                    if i != j:
                        pairs.append((ratings_u[i], ratings_u[j]))

    if not pairs:
        return {
            "alpha": 1.0,
            "observed_disagreement": 0.0,
            "expected_disagreement": 0.0,
            "units": n_units,
            "raters": n_raters,
            "level": level_of_measurement,
            "interpretation": "Insufficient overlapping ratings",
        }

    # All values in coincidence
    all_values = [p[0] for p in pairs]
    unique_vals = sorted(list(set(all_values)))
    val_to_idx = {v: i for i, v in enumerate(unique_vals)}
    n_vals = len(unique_vals)

    # Coincidence matrix
    coinc = np.zeros((n_vals, n_vals), dtype=np.float64)
    for v1, v2 in pairs:
        coinc[val_to_idx[v1], val_to_idx[v2]] += 1.0

    total_pairs = float(len(pairs))

    # Difference function d_ck^2
    d_sq = np.zeros((n_vals, n_vals), dtype=np.float64)
    for i, vi in enumerate(unique_vals):
        for j, vj in enumerate(unique_vals):
            if level_of_measurement == "nominal":
                d_sq[i, j] = 0.0 if vi == vj else 1.0
            elif level_of_measurement == "interval":
                d_sq[i, j] = (float(vi) - float(vj)) ** 2
            else:
                d_sq[i, j] = 0.0 if vi == vj else 1.0

    # Observed disagreement D_o
    d_o = float(np.sum(coinc * d_sq) / total_pairs)

    # Expected disagreement D_e
    marginal = np.sum(coinc, axis=1)  # sum across rows
    n_total = float(np.sum(marginal))
    expected_mat = np.outer(marginal, marginal)
    # Subtract self from diagonal in finite population correction
    for i in range(n_vals):
        expected_mat[i, i] -= marginal[i]
    d_e_denom = n_total * (n_total - 1.0) if n_total > 1.0 else 1.0
    d_e = float(np.sum(expected_mat * d_sq) / d_e_denom)

    if abs(d_e) < 1e-9:
        alpha = 1.0 if abs(d_o) < 1e-9 else 0.0
    else:
        alpha = 1.0 - (d_o / d_e)

    alpha = max(-1.0, min(1.0, alpha))

    # Interpretation (Krippendorff: alpha >= 0.80 reliable, 0.667 <= alpha < 0.80 tentative)
    if alpha >= 0.80:
        interp = "High Reliability (alpha >= 0.80)"
    elif alpha >= 0.67:
        interp = "Tentative Reliability (0.67 <= alpha < 0.80)"
    else:
        interp = "Low Reliability (alpha < 0.67)"

    return {
        "alpha": round(float(alpha), 4),
        "observed_disagreement": round(float(d_o), 4),
        "expected_disagreement": round(float(d_e), 4),
        "units": n_units,
        "raters": n_raters,
        "level": level_of_measurement,
        "interpretation": interp,
    }


def evaluate_ai_assessor_alignment(
    ai_predictions: Sequence[Any],
    assessor_ratings: Sequence[Any],
    numeric_scores: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate AI alignment with human expert assessors.
    If numeric_scores is True, calculates MAE, RMSE, Mean Difference (bias),
    and Pearson correlation.
    If nominal/categorical, calculates exact agreement rate, Cohen's Kappa,
    and confusion analysis.
    """
    if len(ai_predictions) != len(assessor_ratings):
        raise ValueError("AI predictions and assessor ratings must have equal length")

    N = len(ai_predictions)
    if N == 0:
        return {"alignment_rate": 1.0, "sample_size": 0, "verdict": "NO_DATA"}

    if numeric_scores:
        ai_arr = np.array(ai_predictions, dtype=np.float64)
        ass_arr = np.array(assessor_ratings, dtype=np.float64)

        diff = ai_arr - ass_arr
        mean_bias = float(np.mean(diff))  # positive: AI overscores / lenient; negative: AI stricter
        mae = float(np.mean(np.abs(diff)))
        rmse = float(np.sqrt(np.mean(diff ** 2)))

        # Correlation
        std_ai = float(np.std(ai_arr))
        std_ass = float(np.std(ass_arr))
        if std_ai > 1e-6 and std_ass > 1e-6:
            corr = float(np.corrcoef(ai_arr, ass_arr)[0, 1])
        else:
            corr = 1.0 if np.allclose(ai_arr, ass_arr) else 0.0

        if abs(mean_bias) <= 0.05 and corr >= 0.75:
            verdict = "WELL_ALIGNED"
        elif mean_bias > 0.05:
            verdict = "AI_SYSTEMATICALLY_LENIENT"
        elif mean_bias < -0.05:
            verdict = "AI_SYSTEMATICALLY_STRICT"
        else:
            verdict = "MODERATE_ALIGNMENT"

        return {
            "mean_bias": round(mean_bias, 4),
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "pearson_correlation": round(corr, 4),
            "sample_size": N,
            "verdict": verdict,
            "assessor_advisory": (
                "AI provides decision support only. Certified human assessors retain final grading authority."
            ),
        }
    else:
        # Categorical alignment
        matches = sum(1 for a, b in zip(ai_predictions, assessor_ratings) if a == b)
        agreement_rate = matches / float(N)
        kappa_res = compute_cohen_kappa(ai_predictions, assessor_ratings)

        if agreement_rate >= 0.85:
            verdict = "STRONG_ALIGNMENT"
        elif agreement_rate >= 0.70:
            verdict = "ACCEPTABLE_ALIGNMENT"
        else:
            verdict = "DISCREPANT_ALIGNMENT"

        return {
            "agreement_rate": round(agreement_rate, 4),
            "cohen_kappa": kappa_res["kappa"],
            "kappa_interpretation": kappa_res["interpretation"],
            "sample_size": N,
            "verdict": verdict,
            "assessor_advisory": (
                "AI recommendations are advisory. Discrepancies should trigger human review."
            ),
        }
