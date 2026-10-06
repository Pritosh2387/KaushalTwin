"""
Tests: Module 2 — Skill Extraction & NOS Mapping
"""

import pytest
from app.providers.skill_provider import (
    DemoSkillExtractionProvider,
    normalise_with_glossary,
    get_skill_extraction_provider,
)
from app.services.skill_service import (
    extract_skills,
    map_skills_to_nos,
    search_nos,
    get_all_nos,
    get_nos_by_id,
)
from app.algorithms.similarity import (
    cosine_similarity,
    keyword_overlap_score,
    tfidf_similarity,
    exact_match_score,
    HybridScorer,
)


class TestSkillExtraction:
    def setup_method(self):
        self.provider = DemoSkillExtractionProvider()

    def test_extracts_house_wiring(self):
        text = "I have been doing house wiring for 7 years."
        skills = self.provider.extract_skills(text)
        names = [s["normalized_name"] for s in skills]
        assert any("wiring" in n for n in names)

    def test_extracts_switch_installation(self):
        text = "I install switches and fans."
        skills = self.provider.extract_skills(text)
        names = [s["normalized_name"] for s in skills]
        assert any("switch" in n for n in names)

    def test_extracts_fan_installation(self):
        text = "I install ceiling fans and fans."
        skills = self.provider.extract_skills(text)
        names = [s["normalized_name"] for s in skills]
        assert any("fan" in n for n in names)

    def test_extracts_fault_diagnosis(self):
        text = "I find faults using a tester."
        skills = self.provider.extract_skills(text)
        names = [s["normalized_name"] for s in skills]
        assert any("fault" in n or "test" in n for n in names)

    def test_hindi_transcript_extracts_skills(self):
        text = "Main switch lagata hoon aur pankha lagata hoon. Ghar ki wiring karta hoon."
        skills = self.provider.extract_skills(text, language="hi")
        assert len(skills) > 0

    def test_confidence_is_deterministic(self):
        text = "I install switches."
        skills1 = self.provider.extract_skills(text)
        skills2 = self.provider.extract_skills(text)
        assert skills1 == skills2, "Skill extraction must be deterministic"

    def test_confidence_not_random(self):
        text = "I install switches and fans."
        skills = self.provider.extract_skills(text)
        for s in skills:
            assert 0.0 <= s["confidence"] <= 1.0
            assert isinstance(s["confidence"], float)

    def test_no_skills_from_empty_text(self):
        skills = self.provider.extract_skills("")
        assert skills == []

    def test_returns_evidence_text(self):
        text = "I install switches and do house wiring."
        skills = self.provider.extract_skills(text)
        for s in skills:
            assert s.get("evidence_text"), "evidence_text must not be empty"


class TestGlossaryNormalisation:
    def test_line_tester_normalised(self):
        result = normalise_with_glossary("line tester")
        assert result == "voltage tester"

    def test_hindi_switch_lagana(self):
        result = normalise_with_glossary("switch lagana")
        assert result == "switch installation"

    def test_unknown_term_returned_lowercase(self):
        result = normalise_with_glossary("some unknown term")
        assert result == "some unknown term"

    def test_alias_matches(self):
        result = normalise_with_glossary("phase tester")
        assert result == "voltage tester"


class TestNOSMappingService:
    def test_mapping_returns_candidates(self):
        skills = [{"skill_name": "house wiring", "normalized_name": "house wiring",
                   "evidence_text": "I do house wiring", "confidence": 0.90}]
        mappings = map_skills_to_nos(skills, top_k=3)
        assert len(mappings) == 1
        assert len(mappings[0]["candidates"]) <= 3

    def test_candidates_have_required_fields(self):
        skills = [{"skill_name": "switch installation", "normalized_name": "switch installation",
                   "evidence_text": "I install switches", "confidence": 0.92}]
        mappings = map_skills_to_nos(skills)
        for candidate in mappings[0]["candidates"]:
            assert "nos_id" in candidate
            assert "similarity" in candidate
            assert "mapping_status" in candidate
            assert candidate["mapping_status"] == "SUGGESTED"

    def test_mapping_never_certified(self):
        skills = [{"skill_name": "earthing", "normalized_name": "earthing installation",
                   "evidence_text": "I do earthing", "confidence": 0.85}]
        mappings = map_skills_to_nos(skills)
        for candidate in mappings[0]["candidates"]:
            assert candidate["mapping_status"] == "SUGGESTED"
            assert candidate["mapping_status"] != "CERTIFIED"

    def test_candidates_ranked_by_similarity(self):
        skills = [{"skill_name": "fault diagnosis", "normalized_name": "electrical fault diagnosis",
                   "evidence_text": "fault check", "confidence": 0.88}]
        mappings = map_skills_to_nos(skills, top_k=5)
        sims = [c["similarity"] for c in mappings[0]["candidates"]]
        assert sims == sorted(sims, reverse=True)


class TestSimilarityAlgorithms:
    def test_cosine_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-6)

    def test_cosine_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0, abs=1e-6)

    def test_cosine_zero_vector_returns_zero(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert cosine_similarity(a, b) == 0.0

    def test_keyword_overlap_identical(self):
        score = keyword_overlap_score("switch installation", "switch installation")
        assert score == pytest.approx(1.0, abs=0.01)

    def test_keyword_overlap_disjoint(self):
        score = keyword_overlap_score("switch", "earthing")
        assert score == 0.0

    def test_exact_match_true(self):
        assert exact_match_score("switch installation", "switch installation") == 1.0

    def test_exact_match_false(self):
        assert exact_match_score("switch installation", "earthing") == 0.0

    def test_tfidf_similarity_positive(self):
        score = tfidf_similarity("electrical wiring", "wiring electrical installation")
        assert score > 0.0

    def test_hybrid_scorer_returns_breakdown(self):
        scorer = HybridScorer()
        result = scorer.score("switch installation", "Install Switches and sockets")
        assert "combined_score" in result
        assert "keyword_score" in result
        assert "tfidf_score" in result
        assert 0.0 <= result["combined_score"] <= 1.0

    def test_hybrid_scorer_without_embedding(self):
        scorer = HybridScorer()
        result = scorer.score("house wiring", "domestic wiring installation", embedding_score=None)
        assert result["embedding_score"] is None
        assert result["combined_score"] >= 0.0


class TestNOSRepository:
    def test_nos_repository_loads(self):
        nos = get_all_nos()
        assert len(nos) > 0

    def test_all_nos_have_demo_source(self):
        for nos in get_all_nos():
            assert nos.get("source_type") == "DEMO", f"{nos['id']} missing DEMO source_type"

    def test_get_nos_by_id(self):
        nos = get_nos_by_id("DEMO_NOS_001")
        assert nos is not None
        assert nos["id"] == "DEMO_NOS_001"

    def test_get_nos_unknown_id_returns_none(self):
        nos = get_nos_by_id("NONEXISTENT_NOS_999")
        assert nos is None

    def test_nos_search_returns_results(self):
        results = search_nos("electrical wiring installation", top_k=3)
        assert len(results) > 0
        assert results[0]["similarity"] >= results[-1]["similarity"]
