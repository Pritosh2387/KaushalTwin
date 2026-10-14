"""
KaushalTwin ML Service — Confidence Calibration & Reliability Engine
Module 10: Real-World Evaluation, Calibration & Fairness Auditing

Maintains strict separation between:
1. RAW_SIMILARITY: Multi-signal hybrid similarity score in [0.0, 1.0].
2. HEURISTIC_EXTRACTION_CONFIDENCE: Rule/regex/LLM confidence in entity identification.
3. EVIDENCE_CONFIDENCE: Quality/authenticity rating of documentary or practical evidence.
4. COMPETENCY_SCORE: Assessed performance score across rubric criteria [0.0, 1.0] or [0, 100].
5. CALIBRATED_PROBABILITY: Statistically calibrated probability P(Y=1 | score) of true ground-truth match.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class ScoreSemantics(str, Enum):
    """Explicit score semantics to prevent mixing incompatible quantities."""
    RAW_SIMILARITY = "RAW_SIMILARITY"
    HEURISTIC_EXTRACTION_CONFIDENCE = "HEURISTIC_EXTRACTION_CONFIDENCE"
    EVIDENCE_CONFIDENCE = "EVIDENCE_CONFIDENCE"
    COMPETENCY_SCORE = "COMPETENCY_SCORE"
    CALIBRATED_PROBABILITY = "CALIBRATED_PROBABILITY"


def assert_score_semantic(value: float, score_type: ScoreSemantics, name: str = "score") -> None:
    """Validate score domain and semantics."""
    if not isinstance(value, (int, float)) or math.isnan(value):
        raise ValueError(f"{name} must be a valid numeric quantity, got: {value}")
    if score_type in [ScoreSemantics.RAW_SIMILARITY, ScoreSemantics.HEURISTIC_EXTRACTION_CONFIDENCE,
                      ScoreSemantics.EVIDENCE_CONFIDENCE, ScoreSemantics.CALIBRATED_PROBABILITY]:
        if value < -1e-5 or value > 1.0 + 1e-5:
            raise ValueError(f"{name} with semantic {score_type.value} must be in [0.0, 1.0], got {value}")
    elif score_type == ScoreSemantics.COMPETENCY_SCORE:
        if value < -1e-5 or value > 100.0 + 1e-5:
            raise ValueError(f"{name} with semantic COMPETENCY_SCORE must be in [0.0, 100.0] or [0.0, 1.0], got {value}")


# ---------------------------------------------------------------------------
# Calibration Algorithms
# ---------------------------------------------------------------------------

class PlattScaler:
    """
    Platt Scaling (Logistic Sigmoid Calibration).
    Maps raw similarity scores into calibrated empirical probabilities:
    P(Y=1 | s) = 1 / (1 + exp(A * s + B))
    """

    def __init__(self, A: float = -5.0, B: float = 2.0):
        # Default initialization maps ~0.4 -> 0.5, >0.6 -> high, <0.2 -> low
        self.A = float(A)
        self.B = float(B)
        self.is_fitted = False

    def fit(self, scores: List[float], labels: List[int], max_iter: int = 100, lr: float = 0.05) -> PlattScaler:
        """
        Fit logistic calibration parameters A and B via regularized maximum likelihood.
        Uses target smoothing (Bayesian Laplace smoothing) to prevent overfitting on small samples.
        """
        if len(scores) < 3 or len(set(labels)) < 2:
            # Insufficient class diversity to re-estimate; keep sensible default
            self.is_fitted = True
            return self

        N = len(scores)
        N_pos = sum(labels)
        N_neg = N - N_pos

        # Target smoothing (Platt 1999)
        t_pos = (N_pos + 1.0) / (N_pos + 2.0)
        t_neg = 1.0 / (N_neg + 2.0)
        targets = np.array([t_pos if y == 1 else t_neg for y in labels], dtype=np.float64)
        s = np.array(scores, dtype=np.float64)

        # Gradient descent with small L2 weight decay
        A = self.A
        B = self.B
        lambda_reg = 1e-4

        for _ in range(max_iter):
            # Sigmoid P = 1 / (1 + exp(A*s + B))
            logits = A * s + B
            # Numerical stabilization for exp
            logits_clipped = np.clip(logits, -30.0, 30.0)
            p = 1.0 / (1.0 + np.exp(logits_clipped))

            # Gradients of negative log-likelihood
            err = p - targets
            grad_A = np.mean(err * s) + lambda_reg * A
            grad_B = np.mean(err)

            A -= lr * grad_A
            B -= lr * grad_B

        self.A = float(A)
        self.B = float(B)
        self.is_fitted = True
        return self

    def predict_proba(self, scores: Union[float, List[float]]) -> Union[float, List[float]]:
        """Compute calibrated probability P(Y=1 | score)."""
        single = isinstance(scores, (int, float))
        s_arr = np.array([scores] if single else scores, dtype=np.float64)
        logits = np.clip(self.A * s_arr + self.B, -30.0, 30.0)
        probs = 1.0 / (1.0 + np.exp(logits))
        res = [round(float(p), 4) for p in probs]
        return res[0] if single else res


class IsotonicCalibrator:
    """
    Non-parametric Isotonic Regression using the Pool Adjacent Violators Algorithm (PAVA).
    Produces monotonic piecewise constant calibrated probabilities.
    """

    def __init__(self):
        self.cutoffs: List[float] = []
        self.values: List[float] = []
        self.is_fitted = False

    def fit(self, scores: List[float], labels: List[int]) -> IsotonicCalibrator:
        """Fit isotonic calibration curve."""
        if not scores:
            return self

        # Sort by score
        order = np.argsort(scores)
        s_sorted = [scores[i] for i in order]
        y_sorted = [float(labels[i]) for i in order]

        # PAVA implementation
        # Each block: [weight, sum_y, mean_y, min_s, max_s]
        blocks = [[1.0, y, y, s, s] for s, y in zip(s_sorted, y_sorted)]

        i = 0
        while i < len(blocks) - 1:
            if blocks[i][2] > blocks[i + 1][2]:
                # Violates monotonicity: pool adjacent blocks
                w_new = blocks[i][0] + blocks[i + 1][0]
                sum_new = blocks[i][1] + blocks[i + 1][1]
                mean_new = sum_new / w_new
                s_min = blocks[i][3]
                s_max = blocks[i + 1][4]
                blocks[i] = [w_new, sum_new, mean_new, s_min, s_max]
                del blocks[i + 1]
                if i > 0:
                    i -= 1
            else:
                i += 1

        self.cutoffs = [b[4] for b in blocks]
        self.values = [round(b[2], 4) for b in blocks]
        self.is_fitted = True
        return self

    def predict_proba(self, scores: Union[float, List[float]]) -> Union[float, List[float]]:
        """Predict calibrated probabilities via monotonic step interpolation."""
        single = isinstance(scores, (int, float))
        s_list = [scores] if single else scores

        if not self.is_fitted or not self.values:
            # Fallback to identity score
            return scores

        res = []
        for s in s_list:
            idx = 0
            while idx < len(self.cutoffs) and s > self.cutoffs[idx]:
                idx += 1
            val = self.values[min(idx, len(self.values) - 1)]
            res.append(val)

        return res[0] if single else res


# ---------------------------------------------------------------------------
# Calibration Metrics: ECE, MCE, Brier Score & Reliability Diagrams
# ---------------------------------------------------------------------------

def calculate_ece(
    probabilities: List[float],
    labels: List[int],
    n_bins: int = 10,
) -> Dict[str, Any]:
    """
    Calculate Expected Calibration Error (ECE) and Maximum Calibration Error (MCE).

    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    MCE = max_m |acc(B_m) - conf(B_m)|
    """
    if len(probabilities) != len(labels) or not probabilities:
        return {"ece": 0.0, "mce": 0.0, "brier_score": 0.0, "sample_count": 0}

    probs = np.array(probabilities, dtype=np.float64)
    y = np.array(labels, dtype=np.float64)
    N = len(probs)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    bin_details = []

    for i in range(n_bins):
        low = bin_boundaries[i]
        high = bin_boundaries[i + 1]

        # Points in bin: [low, high) or [low, high] for the last bin
        if i == n_bins - 1:
            in_bin = (probs >= low) & (probs <= high)
        else:
            in_bin = (probs >= low) & (probs < high)

        count = int(np.sum(in_bin))
        if count > 0:
            mean_conf = float(np.mean(probs[in_bin]))
            emp_acc = float(np.mean(y[in_bin]))
            gap = abs(emp_acc - mean_conf)

            ece += (count / N) * gap
            mce = max(mce, gap)

            bin_details.append({
                "bin_index": i,
                "range": [round(low, 2), round(high, 2)],
                "count": count,
                "mean_confidence": round(mean_conf, 4),
                "empirical_accuracy": round(emp_acc, 4),
                "calibration_gap": round(gap, 4),
            })

    # Brier score: mean squared error
    brier = float(np.mean((probs - y) ** 2))

    return {
        "ece": round(float(ece), 4),
        "mce": round(float(mce), 4),
        "brier_score": round(brier, 4),
        "sample_count": N,
        "n_bins": n_bins,
        "active_bins": len(bin_details),
        "reliability_bins": bin_details,
    }


def generate_reliability_diagram(
    probabilities: List[float],
    labels: List[int],
    n_bins: int = 10,
) -> List[Dict[str, Any]]:
    """Return structured reliability diagram bins for visualization."""
    ece_result = calculate_ece(probabilities, labels, n_bins=n_bins)
    return ece_result.get("reliability_bins", [])
