"""
API Integration Tests — All endpoints across all 5 modules
"""

import base64
import pytest
from fastapi.testclient import TestClient
from ml.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Module 1 — Preprocessing
# ---------------------------------------------------------------------------

class TestPreprocessAPI:
    def test_preprocess_english(self):
        r = client.post("/api/v1/ml/preprocess/text", json={
            "text": "I install switches and fans.",
            "language": "en",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["original_text"] == "I install switches and fans."
        assert "normalized_text" in data
        assert len(data["tokens"]) > 0

    def test_preprocess_hindi(self):
        r = client.post("/api/v1/ml/preprocess/text", json={
            "text": "मैं बिजली का काम करता हूँ।",
        })
        assert r.status_code == 200
        assert r.json()["language"] == "hi"

    def test_preprocess_empty_text_rejected(self):
        r = client.post("/api/v1/ml/preprocess/text", json={"text": "   "})
        assert r.status_code == 422

    def test_preprocess_preserves_original(self):
        original = "  Switch   Installation  "
        r = client.post("/api/v1/ml/preprocess/text", json={"text": original})
        assert r.status_code == 200
        assert r.json()["original_text"] == original


# ---------------------------------------------------------------------------
# Module 2 — Skills & NOS Mapping
# ---------------------------------------------------------------------------

DEMO_TRANSCRIPT = (
    "I have been doing house wiring for seven years. "
    "I install switches and fans. I find faults using a line tester."
)

class TestSkillsAPI:
    def test_extract_skills(self):
        r = client.post("/api/v1/ml/skills/extract", json={
            "text": DEMO_TRANSCRIPT,
            "language": "en",
            "trade": "electrician",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        assert len(data["skills"]) > 0

    def test_skills_have_required_fields(self):
        r = client.post("/api/v1/ml/skills/extract", json={"text": DEMO_TRANSCRIPT})
        assert r.status_code == 200
        for skill in r.json()["skills"]:
            assert "skill_name" in skill
            assert "normalized_name" in skill
            assert "confidence" in skill
            assert 0 <= skill["confidence"] <= 1

    def test_extract_empty_text_rejected(self):
        r = client.post("/api/v1/ml/skills/extract", json={"text": ""})
        assert r.status_code == 422

    def test_nos_map_endpoint(self):
        skills = [{"skill_name": "house wiring", "normalized_name": "house wiring",
                   "evidence_text": "house wiring", "confidence": 0.90}]
        r = client.post("/api/v1/ml/nos/map", json={"skills": skills, "top_k": 3})
        assert r.status_code == 200
        data = r.json()
        assert len(data["mappings"]) == 1
        assert len(data["mappings"][0]["candidates"]) <= 3

    def test_nos_mapping_always_suggested(self):
        skills = [{"skill_name": "earthing", "normalized_name": "earthing installation",
                   "evidence_text": "I do earthing", "confidence": 0.85}]
        r = client.post("/api/v1/ml/nos/map", json={"skills": skills})
        assert r.status_code == 200
        for mapping in r.json()["mappings"]:
            for c in mapping["candidates"]:
                assert c["mapping_status"] == "SUGGESTED"

    def test_nos_search(self):
        r = client.post("/api/v1/ml/nos/search", json={"query": "electrical wiring", "top_k": 3})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] <= 3
        assert len(data["results"]) > 0

    def test_list_nos(self):
        r = client.get("/api/v1/ml/nos")
        assert r.status_code == 200
        assert r.json()["count"] > 0

    def test_get_nos_by_id(self):
        r = client.get("/api/v1/ml/nos/DEMO_NOS_001")
        assert r.status_code == 200
        assert r.json()["id"] == "DEMO_NOS_001"

    def test_get_nos_not_found(self):
        r = client.get("/api/v1/ml/nos/FAKE_NOS_999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Module 3 — Competency Twin
# ---------------------------------------------------------------------------

DEMO_CRITERIA = [
    {"name": "tool selection", "score": 4, "weight": 0.2, "max_score": 5},
    {"name": "procedure", "score": 5, "weight": 0.3, "max_score": 5},
    {"name": "execution", "score": 4, "weight": 0.5, "max_score": 5},
]

class TestCompetencyAPI:
    def test_score_single_nos(self):
        r = client.post("/api/v1/ml/competency/score", json={
            "nos_id": "DEMO_NOS_004",
            "criteria": DEMO_CRITERIA,
            "mandatory": True,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["nos_id"] == "DEMO_NOS_004"
        assert 0 <= data["competency_score"] <= 100
        assert data["evidence_confidence"] is None  # null until future module

    def test_competency_status_valid(self):
        r = client.post("/api/v1/ml/competency/score", json={
            "nos_id": "DEMO_NOS_001",
            "criteria": DEMO_CRITERIA,
        })
        assert r.status_code == 200
        assert r.json()["status"] in ("UNASSESSED", "IN_PROGRESS", "EVIDENCE_AVAILABLE")

    def test_build_twin_multi_nos(self):
        r = client.post("/api/v1/ml/competency/twin", json={
            "worker_id": "W001",
            "competencies": [
                {"nos_id": "DEMO_NOS_001", "criteria": DEMO_CRITERIA, "mandatory": True},
                {"nos_id": "DEMO_NOS_004", "criteria": DEMO_CRITERIA, "mandatory": True},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["worker_id"] == "W001"
        assert len(data["competencies"]) == 2
        assert data["summary"]["total_nos"] == 2

    def test_empty_criteria_rejected(self):
        r = client.post("/api/v1/ml/competency/score", json={
            "nos_id": "DEMO_NOS_001",
            "criteria": [],  # min_length=1
        })
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Module 4 — Evidence
# ---------------------------------------------------------------------------

class TestEvidenceAPI:
    def test_analyse_evidence(self):
        r = client.post("/api/v1/ml/evidence/analyze", json={
            "evidence": [
                {"source": "PRACTICAL", "supports": True},
                {"source": "SELF_DECLARATION", "supports": True},
            ]
        })
        assert r.status_code == 200
        data = r.json()
        assert "support_score" in data
        assert "conflict" in data

    def test_conflict_detected(self):
        r = client.post("/api/v1/ml/evidence/conflict", json={
            "evidence": [
                {"source": "SELF_DECLARATION", "supports": True},
                {"source": "PRACTICAL", "supports": False},
            ]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["conflict"] is True
        assert data["severity"] is not None

    def test_no_conflict(self):
        r = client.post("/api/v1/ml/evidence/conflict", json={
            "evidence": [{"source": "PRACTICAL", "supports": True}]
        })
        assert r.status_code == 200
        assert r.json()["conflict"] is False

    def test_hash_endpoint(self):
        content = base64.b64encode(b"hello evidence file").decode()
        r = client.post("/api/v1/ml/evidence/hash", json={"content_base64": content})
        assert r.status_code == 200
        data = r.json()
        assert data["integrity_status"] == "VERIFIED"
        assert len(data["sha256"]) == 64

    def test_hash_invalid_base64(self):
        r = client.post("/api/v1/ml/evidence/hash", json={"content_base64": "NOT_VALID_BASE64!!!"})
        assert r.status_code == 422

    def test_duplicate_check(self):
        h = base64.b64encode(b"content").decode()
        import hashlib
        digest = hashlib.sha256(b"content").hexdigest()
        r = client.post("/api/v1/ml/evidence/duplicates", json={"hashes": [digest, digest, "other"]})
        assert r.status_code == 200
        data = r.json()
        assert data["has_duplicates"] is True


# ---------------------------------------------------------------------------
# Module 5 — Assessment
# ---------------------------------------------------------------------------

DEMO_COMPETENCY_STATES = [
    {"nos_id": "DEMO_NOS_004", "mandatory": True, "importance": 1.0, "weight": 1.0,
     "evidence_confidence": 0.35, "evidence_coverage": 0.2, "competency_score": 40},
    {"nos_id": "DEMO_NOS_005", "mandatory": True, "importance": 0.9, "weight": 0.9,
     "evidence_confidence": None, "evidence_coverage": 0.4, "competency_score": 60},
    {"nos_id": "DEMO_NOS_009", "mandatory": False, "importance": 0.5, "weight": 0.5,
     "evidence_confidence": None, "evidence_coverage": 0.8, "competency_score": 80},
]

class TestAssessmentAPI:
    def test_next_task(self):
        r = client.post("/api/v1/ml/assessment/next-task", json={
            "competency_states": DEMO_COMPETENCY_STATES,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["selected_task"] is not None
        assert "priority_score" in data
        assert isinstance(data["reason"], list)

    def test_next_task_deterministic(self):
        payload = {"competency_states": DEMO_COMPETENCY_STATES}
        r1 = client.post("/api/v1/ml/assessment/next-task", json=payload)
        r2 = client.post("/api/v1/ml/assessment/next-task", json=payload)
        assert r1.json()["selected_task"]["id"] == r2.json()["selected_task"]["id"]

    def test_rank_tasks(self):
        r = client.post("/api/v1/ml/assessment/rank-tasks", json={
            "competency_states": DEMO_COMPETENCY_STATES,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        scores = [t["priority_score"] for t in data["ranked_tasks"]]
        assert scores == sorted(scores, reverse=True)

    def test_select_variant(self):
        r = client.post("/api/v1/ml/assessment/select-variant", json={
            "task_id": "TASK_004",
            "seed": 42,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["variant"] is not None

    def test_select_variant_unknown_task(self):
        r = client.post("/api/v1/ml/assessment/select-variant", json={"task_id": "FAKE_TASK"})
        assert r.status_code == 404

    def test_should_continue_true(self):
        r = client.post("/api/v1/ml/assessment/should-continue", json={
            "competency_states": DEMO_COMPETENCY_STATES,
            "coverage_threshold": 0.8,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["should_continue"] is True
        assert len(data["mandatory_gaps"]) > 0


# ---------------------------------------------------------------------------
# Unified Pipeline
# ---------------------------------------------------------------------------

class TestPipelineAPI:
    def test_full_pipeline(self):
        r = client.post("/api/v1/ml/pipeline/worker-assessment", json={
            "worker_id": "W001",
            "language": "en",
            "trade": "electrician",
            "transcript": DEMO_TRANSCRIPT,
            "competencies": [],
            "evidence": [],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["worker_id"] == "W001"
        assert len(data["skills"]) > 0
        assert len(data["nos_candidates"]) > 0
        assert "competency_twin" in data
        assert "continuation" in data

    def test_pipeline_with_competencies(self):
        r = client.post("/api/v1/ml/pipeline/worker-assessment", json={
            "worker_id": "W002",
            "language": "en",
            "trade": "electrician",
            "transcript": "I do house wiring and install fans.",
            "competencies": [
                {"nos_id": "DEMO_NOS_004", "criteria": DEMO_CRITERIA, "mandatory": True},
            ],
            "evidence": [
                {"source": "SELF_DECLARATION", "supports": True},
                {"source": "PRACTICAL", "supports": False},
            ],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["evidence_features"] is not None
        assert data["evidence_features"]["conflict"] is True

    def test_pipeline_empty_transcript_rejected(self):
        r = client.post("/api/v1/ml/pipeline/worker-assessment", json={
            "worker_id": "W001",
            "transcript": "",
        })
        assert r.status_code == 422
