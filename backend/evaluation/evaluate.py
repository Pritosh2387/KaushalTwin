"""
KaushalTwin ML Service — Evaluation Scaffolding
IMPORTANT: All results are SYNTHETIC / DEMO VALIDATION only.
No real-world accuracy claims are made.

This script provides reusable evaluation utilities for:
1. NOS mapping Top-1 / Top-3 accuracy
2. Competency scoring consistency
3. Task selection coverage
4. Evidence conflict detection accuracy

Run with: python evaluation/evaluate.py
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Allow running from ml_service root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.providers.skill_provider import DemoSkillExtractionProvider
from ml.services.skill_service import map_skills_to_nos
from ml.algorithms.competency_score import weighted_competency_score
from ml.algorithms.evidence_features import extract_evidence_features
from ml.algorithms.task_selector import rank_tasks, select_next_task


# ---------------------------------------------------------------------------
# Synthetic labelled dataset for demo evaluation
# ---------------------------------------------------------------------------

NOS_MAPPING_TEST_CASES = [
    # (skill_name, normalized_skill, expected_top1_nos_id, expected_top3_nos_ids)
    ("switch installation", "switch installation", "DEMO_NOS_003",
     ["DEMO_NOS_003", "DEMO_NOS_002", "DEMO_NOS_010"]),
    ("house wiring", "house wiring", "DEMO_NOS_002",
     ["DEMO_NOS_002", "DEMO_NOS_003", "DEMO_NOS_010"]),
    ("fault diagnosis", "electrical fault diagnosis", "DEMO_NOS_005",
     ["DEMO_NOS_005", "DEMO_NOS_008", "DEMO_NOS_010"]),
    ("earthing", "earthing installation", "DEMO_NOS_007",
     ["DEMO_NOS_007", "DEMO_NOS_004", "DEMO_NOS_009"]),
    ("safe isolation", "safe isolation", "DEMO_NOS_004",
     ["DEMO_NOS_004", "DEMO_NOS_009", "DEMO_NOS_007"]),
]

COMPETENCY_SCORE_TEST_CASES = [
    # (criteria, expected_score_approx)
    ([{"name": "c1", "score": 5, "weight": 1.0, "max_score": 5}], 100),
    ([{"name": "c1", "score": 0, "weight": 1.0, "max_score": 5}], 0),
    ([
        {"name": "c1", "score": 4, "weight": 0.5, "max_score": 5},
        {"name": "c2", "score": 3, "weight": 0.5, "max_score": 5},
    ], 70),  # (4+3)/2 /5 * 100 = 70
]

CONFLICT_TEST_CASES = [
    # (evidence_list, expected_conflict)
    ([{"source": "SELF_DECLARATION", "supports": True},
      {"source": "PRACTICAL", "supports": False}], True),
    ([{"source": "PRACTICAL", "supports": True},
      {"source": "ASSESSED", "supports": True}], False),
    ([{"source": "SELF_DECLARATION", "supports": True}], False),
]


# ---------------------------------------------------------------------------
# Evaluation functions
# ---------------------------------------------------------------------------

def evaluate_nos_mapping(top_k: int = 3) -> dict:
    """
    SYNTHETIC DEMO VALIDATION — NOT real-world accuracy.
    Evaluates NOS mapping against a hand-labelled demo set.
    """
    top1_hits = 0
    topk_hits = 0
    total = len(NOS_MAPPING_TEST_CASES)

    print("\n--- NOS Mapping Evaluation (SYNTHETIC/DEMO) ---")
    for skill_name, norm_name, expected_top1, expected_topk in NOS_MAPPING_TEST_CASES:
        skills = [{"skill_name": skill_name, "normalized_name": norm_name,
                   "evidence_text": skill_name, "confidence": 0.8}]
        mappings = map_skills_to_nos(skills, top_k=top_k)
        candidates = mappings[0]["candidates"] if mappings else []
        candidate_ids = [c["nos_id"] for c in candidates]

        top1_match = len(candidates) > 0 and candidates[0]["nos_id"] == expected_top1
        topk_match = expected_top1 in candidate_ids

        if top1_match:
            top1_hits += 1
        if topk_match:
            topk_hits += 1

        status = "TOP1-HIT" if top1_match else ("TOPK-HIT" if topk_match else "MISS")
        print(f"  [{status}] '{norm_name}' => got {candidate_ids[:3]} (expected {expected_top1})")

    top1_acc = top1_hits / total
    topk_acc = topk_hits / total
    print(f"\n  Top-1 accuracy : {top1_acc:.0%}  ({top1_hits}/{total}) [SYNTHETIC]")
    print(f"  Top-{top_k} accuracy: {topk_acc:.0%}  ({topk_hits}/{total}) [SYNTHETIC]")
    print("  NOTE: These numbers reflect demo data only. Real accuracy requires official NOS labels.")
    return {"top1_accuracy": top1_acc, "topk_accuracy": topk_acc, "type": "SYNTHETIC_DEMO"}


def evaluate_competency_scoring() -> dict:
    """
    Test weighted scoring consistency.
    All results are mathematical — no real-world claim.
    """
    print("\n--- Competency Scoring Consistency ---")
    passed = 0
    for criteria, expected_approx in COMPETENCY_SCORE_TEST_CASES:
        result = weighted_competency_score(criteria)
        score = result["competency_score"]
        ok = abs(score - expected_approx) <= 5  # tolerance ±5
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"  [{status}] expected~{expected_approx}  got={score}")
    print(f"\n  Passed: {passed}/{len(COMPETENCY_SCORE_TEST_CASES)}")
    return {"passed": passed, "total": len(COMPETENCY_SCORE_TEST_CASES)}


def evaluate_conflict_detection() -> dict:
    """Test evidence conflict detection on synthetic cases."""
    print("\n--- Evidence Conflict Detection ---")
    passed = 0
    for evidence, expected_conflict in CONFLICT_TEST_CASES:
        result = extract_evidence_features(evidence)
        got = result["conflict"]
        ok = got == expected_conflict
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        sources = [e["source"] for e in evidence]
        print(f"  [{status}] sources={sources}  expected={expected_conflict}  got={got}")
    print(f"\n  Passed: {passed}/{len(CONFLICT_TEST_CASES)}")
    return {"passed": passed, "total": len(CONFLICT_TEST_CASES)}


def evaluate_task_selection_coverage() -> dict:
    """
    Verify task selection covers mandatory NOS.
    """
    print("\n--- Task Selection Coverage ---")
    from ml.services.task_selection_service import _load_tasks

    tasks = _load_tasks()
    states = {
        "DEMO_NOS_004": {"importance": 1.0, "mandatory": True, "evidence_confidence": 0.2,
                          "evidence_coverage": 0.1, "weight": 1.0},
        "DEMO_NOS_005": {"importance": 0.9, "mandatory": True, "evidence_confidence": None,
                          "evidence_coverage": 0.0, "weight": 0.9},
        "DEMO_NOS_009": {"importance": 0.5, "mandatory": False, "evidence_confidence": 0.9,
                          "evidence_coverage": 0.95, "weight": 0.5},
    }
    selected = select_next_task(tasks, states)
    ranked = rank_tasks(tasks, states)

    print(f"  Selected task  : {selected['id']} -- {selected['title']}")
    print(f"  Priority score : {selected['priority_score']:.4f}")
    print(f"  Reasons        : {selected['reason'][:2]}")
    print(f"  Total ranked   : {len(ranked)}")

    # The selected task should cover a mandatory NOS
    covered_mandatory = any(
        c["nos_id"] in states and states[c["nos_id"]]["mandatory"]
        for c in selected.get("nos_coverage", [])
    )
    status = "PASS" if covered_mandatory else "WARN"
    print(f"  [{status}] Selected task covers a mandatory NOS: {covered_mandatory}")
    return {"selected_task": selected["id"], "covers_mandatory": covered_mandatory}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  KaushalTwin ML Evaluation")
    print("  SYNTHETIC / DEMO VALIDATION — not real-world accuracy")
    print("=" * 60)

    r1 = evaluate_nos_mapping()
    r2 = evaluate_competency_scoring()
    r3 = evaluate_conflict_detection()
    r4 = evaluate_task_selection_coverage()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  NOS Top-1 Accuracy   : {r1['top1_accuracy']:.0%} [SYNTHETIC]")
    print(f"  NOS Top-3 Accuracy   : {r1['topk_accuracy']:.0%} [SYNTHETIC]")
    print(f"  Scoring consistency  : {r2['passed']}/{r2['total']}")
    print(f"  Conflict detection   : {r3['passed']}/{r3['total']}")
    print(f"  Task selection (mandatory NOS covered): {r4['covers_mandatory']}")
    print("\n  IMPORTANT: All accuracy figures are computed on a")
    print("  hand-labelled DEMO dataset. They do NOT reflect")
    print("  real-world RPL assessment validity.")
