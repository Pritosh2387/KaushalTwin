"""
KaushalTwin ML Service — Priority 5 Tests
Trade-Agnostic Skill Extraction & Evidence-Grounded NOS/QP Mapping

Covers:
1. Multi-trade extraction (Electrician, Plumber, Welder, Mason, Multi-trade)
2. Natural language variations (informal terms, Hindi/Hinglish, spelling variants)
3. Contextual annotations (text_span, trade_context, extraction_method)
4. Evidence-grounded NOS mapping with multi-signal scoring and match reasons
5. Trade-aware ranking prioritizing aligned trade competencies
6. Threshold-based abstention and ambiguity detection
7. Unknown input / unsupported skill handling (no forced hallucinated mappings)
8. Synthetic deterministic evaluation benchmark (Precision@K and MRR)
"""

import pytest
from ml.providers.skill_provider import (
    DemoSkillExtractionProvider,
    get_skill_extraction_provider,
)
from ml.services.skill_service import (
    extract_skills,
    map_skills_to_nos,
    search_nos,
    get_all_nos,
    get_nos_by_id,
    invalidate_nos_cache,
)
from ml.trade_registry import (
    detect_trade_from_text,
    normalize_skill_via_synonyms,
    TRADE_INDICATORS,
)


# ===========================================================================
# 1. Trade Detection Tests
# ===========================================================================

class TestTradeDetection:
    def test_detect_electrician_unambiguous(self):
        text = "I install ceiling fans and switches using a line tester."
        trade, conf = detect_trade_from_text(text)
        assert trade == "electrician"
        assert conf >= 0.70

    def test_detect_plumber_unambiguous(self):
        text = "I install CPVC water supply pipes and fix toilet cistern leaks."
        trade, conf = detect_trade_from_text(text)
        assert trade == "plumber"
        assert conf >= 0.70

    def test_detect_welder_unambiguous(self):
        text = "I do MIG welding and SMAW stick welding on steel plates."
        trade, conf = detect_trade_from_text(text)
        assert trade == "welder"
        assert conf >= 0.70

    def test_detect_mason_unambiguous(self):
        text = "I lay bricks and mix cement mortar for wall plastering."
        trade, conf = detect_trade_from_text(text)
        assert trade == "mason"
        assert conf >= 0.70

    def test_detect_ambiguous_multi_trade(self):
        text = "I do electrical wiring and also install plumbing drainage pipes."
        trade, conf = detect_trade_from_text(text)
        assert trade == "ambiguous"
        assert conf == 0.50

    def test_detect_general_safety_text(self):
        text = "I always wear safety helmet and boots and follow work orders."
        trade, conf = detect_trade_from_text(text)
        assert trade == "general"
        assert conf == 0.0


# ===========================================================================
# 2. Multi-Trade Skill Extraction Tests
# ===========================================================================

class TestMultiTradeSkillExtraction:
    def setup_method(self):
        self.provider = DemoSkillExtractionProvider()

    def test_plumber_extraction_explicit_trade(self):
        text = "I install CPVC pipes, connect taps and valves, and repair drainage leaks."
        skills = self.provider.extract_skills(text, trade="plumber")
        assert len(skills) >= 2
        names = [s["normalized_name"] for s in skills]
        assert any("pipe" in n for n in names)
        assert any("tap" in n or "leak" in n or "repair" in n for n in names)
        for s in skills:
            assert s["trade_context"] == "plumber"
            assert s["text_span"]
            assert s["extraction_method"] in ("pattern_match", "synonym_expand")

    def test_welder_extraction_explicit_trade(self):
        text = "I perform MIG welding, arc welding, and inspect completed welds for defects."
        skills = self.provider.extract_skills(text, trade="welder")
        assert len(skills) >= 2
        names = [s["normalized_name"] for s in skills]
        assert any("welding" in n for n in names)
        assert any("inspection" in n or "inspect" in n or "weld" in n for n in names)
        for s in skills:
            assert s["trade_context"] == "welder"

    def test_mason_extraction_explicit_trade(self):
        text = "I lay bricks to plumb and line, mix mortar, and apply plastering to walls."
        skills = self.provider.extract_skills(text, trade="mason")
        assert len(skills) >= 2
        names = [s["normalized_name"] for s in skills]
        assert any("brick" in n for n in names)
        assert any("mortar" in n or "plaster" in n for n in names)
        for s in skills:
            assert s["trade_context"] == "mason"

    def test_auto_detect_plumber_from_general(self):
        text = "I install CPVC pipes and repair water leaks."
        skills = self.provider.extract_skills(text, trade="general")
        assert len(skills) > 0
        assert any("pipe" in s["normalized_name"] for s in skills)
        assert any(s["trade_context"] == "plumber" for s in skills)

    def test_auto_detect_welder_from_general(self):
        text = "I do TIG welding and MIG welding on aluminum."
        skills = self.provider.extract_skills(text, trade="general")
        assert len(skills) > 0
        assert any("welding" in s["normalized_name"] for s in skills)
        assert any(s["trade_context"] == "welder" for s in skills)

    def test_auto_detect_mason_from_general(self):
        text = "I lay bricks and mix cement mortar."
        skills = self.provider.extract_skills(text, trade="general")
        assert len(skills) > 0
        assert any("brick" in s["normalized_name"] for s in skills)
        assert any(s["trade_context"] == "mason" for s in skills)

    def test_multi_trade_cross_trade_extraction(self):
        text = "I do house wiring and fix plumbing leaks in the bathroom."
        skills = self.provider.extract_skills(text, trade="general")
        assert len(skills) >= 2
        trades_found = {s["trade_context"] for s in skills}
        assert "electrician" in trades_found
        assert "plumber" in trades_found

    def test_hinglish_plumber_extraction(self):
        text = "Main paani ki pipe lagata hoon aur nali ka blockage kholta hoon."
        skills = self.provider.extract_skills(text, language="hi", trade="plumber")
        assert len(skills) > 0
        names = [s["normalized_name"] for s in skills]
        assert any("pipe" in n or "drain" in n or "blockage" in n for n in names)

    def test_hinglish_welder_extraction(self):
        text = "Welding machine set karta hoon aur welding rod se joint banata hoon."
        skills = self.provider.extract_skills(text, language="hi", trade="welder")
        assert len(skills) > 0

    def test_unsupported_unknown_skill_returns_empty(self):
        text = "I practice quantum teleportation and write poetry about stars."
        skills = self.provider.extract_skills(text, trade="general")
        assert skills == []

    def test_empty_and_whitespace_returns_empty(self):
        assert self.provider.extract_skills("") == []
        assert self.provider.extract_skills("   \t\n  ") == []


# ===========================================================================
# 3. Evidence-Grounded NOS Mapping Tests
# ===========================================================================

class TestEvidenceGroundedNOSMapping:
    @classmethod
    def setup_class(cls):
        invalidate_nos_cache()

    def test_plumber_skill_maps_to_plumber_nos(self):
        skills = [{
            "skill_name": "pipe installation",
            "normalized_name": "pipe installation",
            "evidence_text": "I install CPVC pipes",
            "confidence": 0.90,
            "trade_context": "plumber",
        }]
        mappings = map_skills_to_nos(skills, top_k=3)
        assert len(mappings) == 1
        candidates = mappings[0]["candidates"]
        assert len(candidates) > 0
        # Top candidate should be a plumber NOS
        top_nos = candidates[0]
        assert "DEMO_NOS_P" in top_nos["nos_id"]
        assert top_nos["trade_match"] is True
        assert len(top_nos["match_reasons"]) > 0

    def test_welder_skill_maps_to_welder_nos(self):
        skills = [{
            "skill_name": "arc welding",
            "normalized_name": "arc welding",
            "evidence_text": "MMA arc welding",
            "confidence": 0.92,
            "trade_context": "welder",
        }]
        mappings = map_skills_to_nos(skills, top_k=3)
        assert len(mappings) == 1
        candidates = mappings[0]["candidates"]
        assert len(candidates) > 0
        top_nos = candidates[0]
        assert "DEMO_NOS_W" in top_nos["nos_id"]
        assert top_nos["trade_match"] is True

    def test_mason_skill_maps_to_mason_nos(self):
        skills = [{
            "skill_name": "bricklaying",
            "normalized_name": "bricklaying",
            "evidence_text": "laying bricks to plumb",
            "confidence": 0.93,
            "trade_context": "mason",
        }]
        mappings = map_skills_to_nos(skills, top_k=3)
        assert len(mappings) == 1
        candidates = mappings[0]["candidates"]
        assert len(candidates) > 0
        top_nos = candidates[0]
        assert "DEMO_NOS_M" in top_nos["nos_id"]
        assert top_nos["trade_match"] is True

    def test_trade_aware_ranking_prefers_matching_trade(self):
        # A generic term like 'inspection' should rank higher for the specified trade's inspection NOS
        skill_electrician = [{
            "skill_name": "inspection",
            "normalized_name": "inspection",
            "evidence_text": "inspecting work",
            "confidence": 0.80,
            "trade_context": "electrician",
        }]
        skill_welder = [{
            "skill_name": "inspection",
            "normalized_name": "inspection",
            "evidence_text": "inspecting work",
            "confidence": 0.80,
            "trade_context": "welder",
        }]
        res_elec = map_skills_to_nos(skill_electrician, top_k=5)[0]["candidates"]
        res_weld = map_skills_to_nos(skill_welder, top_k=5)[0]["candidates"]

        # Electrician inspection should rank electrician NOS higher
        elec_top_trades = [c["nos_id"] for c in res_elec[:2]]
        weld_top_trades = [c["nos_id"] for c in res_weld[:2]]
        assert any("DEMO_NOS_0" in nid for nid in elec_top_trades)
        assert any("DEMO_NOS_W" in nid for nid in weld_top_trades)

    def test_candidates_preserve_provenance_and_identifiers(self):
        skills = [{
            "skill_name": "house wiring",
            "normalized_name": "house wiring",
            "evidence_text": "house wiring",
            "confidence": 0.90,
            "trade_context": "electrician",
        }]
        mappings = map_skills_to_nos(skills, top_k=3)
        for c in mappings[0]["candidates"]:
            assert "nos_id" in c
            assert c["source_type"] == "DEMO"
            assert "provenance" in c
            assert c["mapping_status"] == "SUGGESTED"

    def test_match_reasons_contain_signals(self):
        skills = [{
            "skill_name": "pipe installation",
            "normalized_name": "pipe installation",
            "evidence_text": "install pipes",
            "confidence": 0.90,
            "trade_context": "plumber",
        }]
        mappings = map_skills_to_nos(skills, top_k=1)
        reasons = mappings[0]["candidates"][0]["match_reasons"]
        assert isinstance(reasons, list)
        assert len(reasons) > 0
        assert any("keyword" in r.lower() or "criteria" in r.lower() or "trade" in r.lower() or "similarity" in r.lower() for r in reasons)


# ===========================================================================
# 4. Abstention & Ambiguity Tests
# ===========================================================================

class TestAbstentionAndAmbiguity:
    @classmethod
    def setup_class(cls):
        invalidate_nos_cache()

    def test_abstention_on_high_threshold_for_dissimilar_skill(self):
        # A completely unknown skill should abstain when min_similarity_threshold is set
        skills = [{
            "skill_name": "quantum cryptographic key distribution",
            "normalized_name": "quantum key distribution",
            "evidence_text": "quantum keys",
            "confidence": 0.50,
            "trade_context": "general",
        }]
        mappings = map_skills_to_nos(skills, top_k=3, min_similarity_threshold=0.75)
        assert len(mappings) == 1
        assert mappings[0]["abstained"] is True
        assert len(mappings[0]["candidates"]) == 0
        assert "insufficient evidence" in mappings[0]["abstention_reason"].lower()

    def test_no_abstention_when_match_is_confident(self):
        skills = [{
            "skill_name": "house wiring",
            "normalized_name": "house wiring",
            "evidence_text": "house wiring",
            "confidence": 0.90,
            "trade_context": "electrician",
        }]
        mappings = map_skills_to_nos(skills, top_k=3, min_similarity_threshold=0.10)
        assert len(mappings) == 1
        assert mappings[0]["abstained"] is False
        assert len(mappings[0]["candidates"]) > 0

    def test_ambiguity_flag_set_when_top_candidates_are_close(self):
        # Generic 'safety equipment use' may match multiple safety NOS records with close scores
        skills = [{
            "skill_name": "safety equipment use",
            "normalized_name": "safety equipment use",
            "evidence_text": "wearing PPE",
            "confidence": 0.85,
            "trade_context": "general",
        }]
        mappings = map_skills_to_nos(skills, top_k=3, ambiguity_margin=0.20)
        candidates = mappings[0]["candidates"]
        if len(candidates) >= 2 and abs(candidates[0]["similarity"] - candidates[1]["similarity"]) <= 0.20:
            assert candidates[0]["ambiguity_flag"] is True
            assert candidates[1]["ambiguity_flag"] is True


# ===========================================================================
# 5. Deterministic Evaluation Benchmark Fixture
# ===========================================================================

class TestDeterministicEvaluationBenchmark:
    """
    Deterministic evaluation benchmark measuring Precision@K and MRR on a synthetic
    test suite of known skill-to-competency mappings across 4 trades.

    NOTE: This is a synthetic regression benchmark testing the mapping engine against
    a controlled ground-truth reference set. It does NOT claim to represent real-world
    accuracy on actual workers.
    """

    # Ground-truth test pairs: (skill_dict, expected_nos_id_prefix)
    BENCHMARK_CASES = [
        # Electrician
        ({"skill_name": "house wiring", "trade_context": "electrician"}, "DEMO_NOS_002"),
        ({"skill_name": "switch installation", "trade_context": "electrician"}, "DEMO_NOS_003"),
        ({"skill_name": "safe isolation", "trade_context": "electrician"}, "DEMO_NOS_004"),
        ({"skill_name": "electrical fault diagnosis", "trade_context": "electrician"}, "DEMO_NOS_005"),
        ({"skill_name": "distribution board installation", "trade_context": "electrician"}, "DEMO_NOS_006"),
        ({"skill_name": "earthing installation", "trade_context": "electrician"}, "DEMO_NOS_007"),
        # Plumber
        ({"skill_name": "pipe installation", "trade_context": "plumber"}, "DEMO_NOS_P02"),
        ({"skill_name": "drainage installation", "trade_context": "plumber"}, "DEMO_NOS_P03"),
        ({"skill_name": "sanitary fixture installation", "trade_context": "plumber"}, "DEMO_NOS_P04"),
        ({"skill_name": "plumbing leak repair", "trade_context": "plumber"}, "DEMO_NOS_P05"),
        # Welder
        ({"skill_name": "arc welding", "trade_context": "welder"}, "DEMO_NOS_W02"),
        ({"skill_name": "mig welding", "trade_context": "welder"}, "DEMO_NOS_W03"),
        ({"skill_name": "weld inspection", "trade_context": "welder"}, "DEMO_NOS_W04"),
        ({"skill_name": "welding safety", "trade_context": "welder"}, "DEMO_NOS_W05"),
        # Mason
        ({"skill_name": "bricklaying", "trade_context": "mason"}, "DEMO_NOS_M02"),
        ({"skill_name": "plastering", "trade_context": "mason"}, "DEMO_NOS_M03"),
        ({"skill_name": "site safety", "trade_context": "mason"}, "DEMO_NOS_M04"),
    ]

    @classmethod
    def setup_class(cls):
        invalidate_nos_cache()

    def test_precision_at_k_and_mrr(self):
        top_k = 3
        correct_at_1 = 0
        correct_at_k = 0
        reciprocal_ranks = []

        for skill_info, expected_id in self.BENCHMARK_CASES:
            skill_input = [{
                "skill_name": skill_info["skill_name"],
                "normalized_name": skill_info["skill_name"],
                "evidence_text": skill_info["skill_name"],
                "confidence": 0.90,
                "trade_context": skill_info["trade_context"],
            }]
            mapping = map_skills_to_nos(skill_input, top_k=top_k)[0]
            candidate_ids = [c["nos_id"] for c in mapping["candidates"]]

            # Precision@1
            if candidate_ids and candidate_ids[0] == expected_id:
                correct_at_1 += 1

            # Precision@K
            if expected_id in candidate_ids:
                correct_at_k += 1

            # Reciprocal rank
            if expected_id in candidate_ids:
                rank = candidate_ids.index(expected_id) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

        n = len(self.BENCHMARK_CASES)
        p_at_1 = correct_at_1 / n
        p_at_k = correct_at_k / n
        mrr = sum(reciprocal_ranks) / n

        # Assertions on synthetic benchmark thresholds
        assert p_at_1 >= 0.70, f"Precision@1 ({p_at_1:.2f}) below expected 0.70 threshold"
        assert p_at_k >= 0.85, f"Precision@{top_k} ({p_at_k:.2f}) below expected 0.85 threshold"
        assert mrr >= 0.80, f"MRR ({mrr:.2f}) below expected 0.80 threshold"
