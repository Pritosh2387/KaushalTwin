"""
KaushalTwin ML Service — Evidence Feature Extraction
Module 4: Evidence Feature & Integrity Support
"""

from __future__ import annotations

import hashlib
from typing import Optional


# ---------------------------------------------------------------------------
# Source reliability weights
# ---------------------------------------------------------------------------

# PROTOTYPE WEIGHTS — configurable, not empirically validated
# These are defaults only; the caller may supply custom weights.
DEFAULT_SOURCE_WEIGHTS: dict[str, float] = {
    "PRACTICAL": 1.0,
    "ASSESSED": 0.9,
    "OBSERVED": 0.85,
    "EMPLOYER": 0.5,
    "PEER": 0.45,
    "SELF_DECLARATION": 0.2,
    "DECLARED": 0.2,
    "INFERRED": 0.15,
}


def get_source_weight(source: str, custom_weights: Optional[dict[str, float]] = None) -> float:
    """Return reliability weight for an evidence source type."""
    weights = custom_weights or DEFAULT_SOURCE_WEIGHTS
    return weights.get(source.upper(), 0.3)  # unknown → 0.3


# ---------------------------------------------------------------------------
# Evidence feature extraction
# ---------------------------------------------------------------------------

def extract_evidence_features(
    evidence_list: list[dict],
    custom_weights: Optional[dict[str, float]] = None,
) -> dict:
    """
    Given a list of evidence records, extract features useful for the
    future confidence/decision engine.

    Each evidence dict should contain:
        source   : str  — evidence provenance type
        supports : bool — whether this evidence supports the competency

    Returns:
        source_features      — per-item feature dict
        support_score        — weighted score from supporting evidence
        contradict_score     — weighted score from contradicting evidence
        independent_sources  — count of distinct source types
        conflict             — True if both supporting and contradicting high-weight evidence exists
    """
    if not evidence_list:
        return {
            "source_features": [],
            "support_score": 0.0,
            "contradict_score": 0.0,
            "independent_sources": 0,
            "conflict": False,
            "conflict_reason": None,
        }

    source_features = []
    support_weights: list[float] = []
    contradict_weights: list[float] = []
    seen_sources: set[str] = set()

    for ev in evidence_list:
        source = str(ev.get("source", "UNKNOWN")).upper()
        supports = bool(ev.get("supports", True))
        weight = get_source_weight(source, custom_weights)
        seen_sources.add(source)

        feat = {
            "source": source,
            "reliability_weight": round(weight, 4),
            "supports": supports,
            "observed": source in ("PRACTICAL", "ASSESSED", "OBSERVED"),
        }
        source_features.append(feat)

        if supports:
            support_weights.append(weight)
        else:
            contradict_weights.append(weight)

    support_score = round(sum(support_weights) / len(evidence_list), 4)
    contradict_score = round(sum(contradict_weights) / len(evidence_list), 4)
    independent_sources = len(seen_sources)

    # Conflict detection
    conflict, conflict_reason = _detect_conflict(
        support_score, contradict_score, evidence_list, custom_weights
    )

    return {
        "source_features": source_features,
        "support_score": support_score,
        "contradict_score": contradict_score,
        "independent_sources": independent_sources,
        "conflict": conflict,
        "conflict_reason": conflict_reason,
    }


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def _detect_conflict(
    support_score: float,
    contradict_score: float,
    evidence_list: list[dict],
    custom_weights: Optional[dict[str, float]] = None,
) -> tuple[bool, Optional[str]]:
    """
    Detect conflict patterns in the evidence.

    Pattern 1: High self-declaration + contradicting practical evidence.
    Pattern 2: Both supporting and contradicting high-weight evidence.

    Returns (conflict_flag, reason_string).
    """
    sources_supporting = [
        e for e in evidence_list if e.get("supports", True)
    ]
    sources_contradicting = [
        e for e in evidence_list if not e.get("supports", True)
    ]

    has_high_declaration = any(
        str(e.get("source", "")).upper() in ("SELF_DECLARATION", "DECLARED")
        for e in sources_supporting
    )
    has_practical_contradiction = any(
        str(e.get("source", "")).upper() in ("PRACTICAL", "ASSESSED", "OBSERVED")
        for e in sources_contradicting
    )

    if has_high_declaration and has_practical_contradiction:
        return (
            True,
            "Self-declaration supports competency but practical/observed evidence contradicts it.",
        )

    if support_score > 0.3 and contradict_score > 0.3:
        return (
            True,
            "Evidence from multiple sources both supports and contradicts this competency.",
        )

    return False, None


def conflict_severity(
    support_score: float,
    contradict_score: float,
    has_practical_contradiction: bool,
) -> str:
    """Return 'HIGH', 'MEDIUM', or 'LOW' severity for a detected conflict."""
    if has_practical_contradiction and contradict_score > 0.5:
        return "HIGH"
    if contradict_score > 0.3:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# SHA-256 hashing helper
# ---------------------------------------------------------------------------

def calculate_sha256(data: bytes) -> str:
    """Return hex SHA-256 digest for the given bytes."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def find_duplicate_hashes(hashes: list[str]) -> list[list[str]]:
    """
    Find groups of identical hashes (exact duplicate detection).
    Returns a list of groups where each group has len > 1.

    Duplicate detection strategy: exact SHA-256 equality only.
    Perceptual/video similarity is NOT implemented here.
    """
    from collections import defaultdict

    groups: dict[str, list[int]] = defaultdict(list)
    for idx, h in enumerate(hashes):
        groups[h].append(idx)

    return [
        [hashes[i] for i in indices]
        for indices in groups.values()
        if len(indices) > 1
    ]
