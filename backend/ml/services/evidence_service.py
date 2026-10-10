"""
KaushalTwin ML Service — Evidence Service
Module 4: Evidence Feature & Integrity Support
"""

from __future__ import annotations

from ml.algorithms.evidence_features import (
    extract_evidence_features,
    calculate_sha256,
    find_duplicate_hashes,
    conflict_severity,
)


def analyse_evidence(evidence_list: list[dict], custom_weights: dict | None = None) -> dict:
    """
    Analyse a set of evidence records and return feature summary.
    """
    features = extract_evidence_features(evidence_list, custom_weights)
    return features


def detect_conflict(evidence_list: list[dict], custom_weights: dict | None = None) -> dict:
    """
    Focus on conflict detection for a set of evidence records.
    """
    features = extract_evidence_features(evidence_list, custom_weights)
    conflict = features["conflict"]
    reason = features.get("conflict_reason")

    severity = None
    if conflict:
        has_practical = any(
            str(e.get("source", "")).upper() in ("PRACTICAL", "ASSESSED", "OBSERVED")
            and not e.get("supports", True)
            for e in evidence_list
        )
        severity = conflict_severity(
            features["support_score"],
            features["contradict_score"],
            has_practical,
        )

    return {
        "conflict": conflict,
        "reason": reason,
        "severity": severity,
        "support_score": features["support_score"],
        "contradict_score": features["contradict_score"],
    }


def hash_content(content: bytes) -> dict:
    """Calculate SHA-256 hash for file/content integrity."""
    digest = calculate_sha256(content)
    return {
        "sha256": digest,
        "size_bytes": len(content),
        "integrity_status": "VERIFIED",
    }


def check_duplicates(hashes: list[str]) -> dict:
    """Detect exact SHA-256 duplicate groups."""
    groups = find_duplicate_hashes(hashes)
    return {
        "duplicate_groups": groups,
        "has_duplicates": len(groups) > 0,
        "total_hashes": len(hashes),
        "duplicate_count": sum(len(g) - 1 for g in groups),
    }
