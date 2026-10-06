"""
Tests: Module 4 — Evidence Feature Extraction & Integrity
"""

import hashlib
import pytest
from app.algorithms.evidence_features import (
    extract_evidence_features,
    calculate_sha256,
    find_duplicate_hashes,
    conflict_severity,
    get_source_weight,
    DEFAULT_SOURCE_WEIGHTS,
)
from app.services.evidence_service import (
    analyse_evidence,
    detect_conflict,
    hash_content,
    check_duplicates,
)


class TestSourceWeights:
    def test_practical_has_highest_weight(self):
        assert get_source_weight("PRACTICAL") == 1.0

    def test_self_declaration_has_low_weight(self):
        assert get_source_weight("SELF_DECLARATION") <= 0.25

    def test_unknown_source_gets_default(self):
        w = get_source_weight("UNKNOWN_SOURCE")
        assert 0.0 < w < 1.0

    def test_custom_weights_override(self):
        custom = {"PRACTICAL": 0.5}
        w = get_source_weight("PRACTICAL", custom_weights=custom)
        assert w == 0.5

    def test_all_default_weights_in_range(self):
        for source, weight in DEFAULT_SOURCE_WEIGHTS.items():
            assert 0.0 <= weight <= 1.0, f"Weight for {source} out of range"


class TestEvidenceFeatureExtraction:
    def test_pure_support(self):
        evidence = [
            {"source": "PRACTICAL", "supports": True},
            {"source": "ASSESSED", "supports": True},
        ]
        result = extract_evidence_features(evidence)
        assert result["support_score"] > 0
        assert result["contradict_score"] == 0.0
        assert result["conflict"] is False

    def test_conflict_detected_declaration_vs_practical(self):
        evidence = [
            {"source": "SELF_DECLARATION", "supports": True},
            {"source": "PRACTICAL", "supports": False},  # contradicts
        ]
        result = extract_evidence_features(evidence)
        assert result["conflict"] is True
        assert result["conflict_reason"] is not None

    def test_no_evidence_returns_safe_defaults(self):
        result = extract_evidence_features([])
        assert result["conflict"] is False
        assert result["support_score"] == 0.0

    def test_independent_sources_counted(self):
        evidence = [
            {"source": "PRACTICAL", "supports": True},
            {"source": "ASSESSED", "supports": True},
            {"source": "SELF_DECLARATION", "supports": True},
        ]
        result = extract_evidence_features(evidence)
        assert result["independent_sources"] == 3

    def test_observed_flag_set_correctly(self):
        evidence = [
            {"source": "PRACTICAL", "supports": True},
            {"source": "SELF_DECLARATION", "supports": True},
        ]
        result = extract_evidence_features(evidence)
        sources = {f["source"]: f for f in result["source_features"]}
        assert sources["PRACTICAL"]["observed"] is True
        assert sources["SELF_DECLARATION"]["observed"] is False


class TestConflictSeverity:
    def test_high_severity(self):
        sev = conflict_severity(0.2, 0.8, has_practical_contradiction=True)
        assert sev == "HIGH"

    def test_medium_severity(self):
        sev = conflict_severity(0.4, 0.4, has_practical_contradiction=False)
        assert sev == "MEDIUM"

    def test_low_severity(self):
        sev = conflict_severity(0.6, 0.2, has_practical_contradiction=False)
        assert sev == "LOW"


class TestSHA256:
    def test_known_hash(self):
        content = b"hello world"
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert calculate_sha256(content) == expected

    def test_empty_bytes_hash(self):
        result = calculate_sha256(b"")
        assert len(result) == 64  # SHA-256 is 64 hex chars

    def test_different_content_different_hash(self):
        h1 = calculate_sha256(b"file_a")
        h2 = calculate_sha256(b"file_b")
        assert h1 != h2

    def test_same_content_same_hash(self):
        content = b"evidence content"
        assert calculate_sha256(content) == calculate_sha256(content)


class TestDuplicateDetection:
    def test_no_duplicates(self):
        hashes = ["aaa", "bbb", "ccc"]
        groups = find_duplicate_hashes(hashes)
        assert groups == []

    def test_one_duplicate_pair(self):
        hashes = ["aaa", "bbb", "aaa"]
        groups = find_duplicate_hashes(hashes)
        assert len(groups) == 1
        assert len(groups[0]) == 2

    def test_multiple_duplicate_groups(self):
        hashes = ["aaa", "bbb", "aaa", "bbb", "ccc"]
        groups = find_duplicate_hashes(hashes)
        assert len(groups) == 2

    def test_empty_list(self):
        groups = find_duplicate_hashes([])
        assert groups == []


class TestEvidenceService:
    def test_analyse_evidence_service(self):
        evidence = [{"source": "PRACTICAL", "supports": True}]
        result = analyse_evidence(evidence)
        assert "support_score" in result

    def test_detect_conflict_service(self):
        evidence = [
            {"source": "SELF_DECLARATION", "supports": True},
            {"source": "PRACTICAL", "supports": False},
        ]
        result = detect_conflict(evidence)
        assert result["conflict"] is True
        assert result["severity"] is not None

    def test_hash_content_service(self):
        content = b"test evidence content"
        result = hash_content(content)
        assert result["integrity_status"] == "VERIFIED"
        assert len(result["sha256"]) == 64

    def test_check_duplicates_service(self):
        hashes = ["hash1", "hash2", "hash1"]
        result = check_duplicates(hashes)
        assert result["has_duplicates"] is True
        assert result["duplicate_count"] == 1
