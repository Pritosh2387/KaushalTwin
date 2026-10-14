"""
KaushalTwin ML Service — Pipeline Evaluation Framework
Module 10: Real-World Evaluation, Calibration & Fairness Auditing

Executes end-to-end evaluation runs of:
- Skill extraction (Exact & Relaxed Precision/Recall/F1)
- NOS/QP semantic mapping (Top-1, Top-k, MRR)
- Abstention fidelity (FAR, unsafe prediction rate)
- Confidence calibration (ECE, MCE, Brier score, Platt scaling)
- Demographic & trade fairness auditing (Four-Fifths Rule compliance)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

from ml.evaluation.models import EvaluationDataset, EvaluationExample
from ml.evaluation.metrics import (
    evaluate_skill_extraction,
    evaluate_nos_mapping,
    evaluate_abstention,
    aggregate_abstention_metrics,
)
from ml.evaluation.calibration import (
    calculate_ece,
    generate_reliability_diagram,
    PlattScaler,
    ScoreSemantics,
    assert_score_semantic,
)
from ml.evaluation.fairness import audit_fairness_slices
from ml.services.skill_service import extract_skills, map_skills_to_nos


DEFAULT_GROUND_TRUTH_PATH = Path(__file__).resolve().parent.parent / "data" / "evaluation_ground_truth.json"


class PipelineEvaluator:
    """
    Orchestrates end-to-end evaluation of KaushalTwin's skill extraction,
    NOS mapping, abstention, calibration, and fairness engines.
    """

    def __init__(self, dataset: Optional[EvaluationDataset] = None, dataset_path: Optional[Union[str, Path]] = None):
        if dataset is not None:
            self.dataset = dataset
        else:
            path = Path(dataset_path) if dataset_path else DEFAULT_GROUND_TRUTH_PATH
            if not path.exists():
                raise FileNotFoundError(f"Evaluation benchmark dataset not found at {path}")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.dataset = EvaluationDataset.model_validate(data)

    def run_evaluation(
        self,
        top_k: int = 3,
        min_similarity_threshold: float = 0.25,
        token_overlap_threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Execute full evaluation across all examples in the dataset.
        Returns aggregated metrics, calibration statistics, and fairness audit.
        """
        eval_records: List[Dict[str, Any]] = []
        calibration_scores: List[float] = []
        calibration_labels: List[int] = []

        total_examples = len(self.dataset.examples)
        if total_examples == 0:
            return {
                "dataset_id": self.dataset.dataset_id,
                "empirical_status": self.dataset.empirical_status,
                "total_examples": 0,
                "message": "Dataset contains no evaluation examples.",
            }

        for ex in self.dataset.examples:
            # 1. Skill Extraction
            ext_resp = extract_skills(text=ex.worker_statement, language=ex.language, trade=ex.trade)
            raw_skills = ext_resp.skills if hasattr(ext_resp, "skills") else []
            extracted_names = [
                s.get("skill_name") or s.get("normalized_name") if isinstance(s, dict)
                else getattr(s, "skill_name", str(s))
                for s in raw_skills
            ]
            skills_payload = [
                s if isinstance(s, dict) else (s.model_dump() if hasattr(s, "model_dump") else {"skill_name": str(s)})
                for s in raw_skills
            ]

            ext_eval = evaluate_skill_extraction(
                extracted_skills=extracted_names,
                ground_truth_skills=ex.expert_skills,
                token_overlap_threshold=token_overlap_threshold,
            )

            # 2. NOS Mapping
            if skills_payload:
                mapping_res = map_skills_to_nos(
                    skills=skills_payload,
                    top_k=top_k,
                    min_similarity_threshold=min_similarity_threshold,
                )
            else:
                mapping_res = []

            # 3. Abstention Check
            has_valid_mapping = False
            all_candidates: List[Dict[str, Any]] = []

            for m in mapping_res:
                if not m.get("abstained", False) and m.get("candidates"):
                    has_valid_mapping = True
                    all_candidates.extend(m.get("candidates", []))

            predicted_abstained = (len(extracted_names) == 0) or (not has_valid_mapping)
            abst_eval = evaluate_abstention(
                predicted_abstained=predicted_abstained,
                ground_truth_should_abstain=ex.should_abstain,
            )

            # Sort candidate matches by similarity
            all_candidates.sort(key=lambda c: c.get("similarity", 0.0), reverse=True)

            # 4. NOS Mapping Evaluation (only applicable if non-abstention)
            if not ex.should_abstain:
                map_eval = evaluate_nos_mapping(
                    predicted_candidates=all_candidates,
                    ground_truth_ids=ex.expert_nos_ids,
                    acceptable_alternatives=ex.acceptable_alternatives,
                    top_k=top_k,
                )
            else:
                map_eval = {
                    "top_1_accuracy": 0.0,
                    "top_k_accuracy": 0.0,
                    "reciprocal_rank": 0.0,
                    "match_found": False,
                    "match_rank": None,
                    "matched_id": None,
                }

            # 5. Collect Calibration Pairs
            all_valid_nos = set(ex.expert_nos_ids) | set(ex.acceptable_alternatives)
            for cand in all_candidates:
                sim = float(cand.get("similarity", 0.0))
                # Validate score semantics
                assert_score_semantic(sim, ScoreSemantics.RAW_SIMILARITY, name="candidate_similarity")
                cand_id = str(cand.get("nos_id") or cand.get("id") or cand.get("code") or "").strip()
                is_match = 1 if (cand_id in all_valid_nos and not ex.should_abstain) else 0
                calibration_scores.append(sim)
                calibration_labels.append(is_match)

            # Store record
            record = {
                "example_id": ex.example_id,
                "trade": ex.trade,
                "style": ex.style,
                "language": ex.language,
                "should_abstain": ex.should_abstain,
                "predicted_abstained": predicted_abstained,
                "extraction_f1": ext_eval["relaxed_f1"],
                "exact_f1": ext_eval["exact_f1"],
                "mapping_top1": map_eval["top_1_accuracy"],
                "mapping_topk": map_eval["top_k_accuracy"],
                "mapping_mrr": map_eval["reciprocal_rank"],
                "abstention_eval": abst_eval,
                "extraction_eval": ext_eval,
                "mapping_eval": map_eval,
                "extracted_skills": extracted_names,
            }
            eval_records.append(record)

        # -------------------------------------------------------------------
        # Aggregate Metrics Across Entire Evaluation Run
        # -------------------------------------------------------------------

        # Skill Extraction Aggregates
        mean_exact_prec = float(np.mean([r["extraction_eval"]["exact_precision"] for r in eval_records]))
        mean_exact_rec = float(np.mean([r["extraction_eval"]["exact_recall"] for r in eval_records]))
        mean_exact_f1 = float(np.mean([r["extraction_eval"]["exact_f1"] for r in eval_records]))

        mean_rel_prec = float(np.mean([r["extraction_eval"]["relaxed_precision"] for r in eval_records]))
        mean_rel_rec = float(np.mean([r["extraction_eval"]["relaxed_recall"] for r in eval_records]))
        mean_rel_f1 = float(np.mean([r["extraction_eval"]["relaxed_f1"] for r in eval_records]))

        # Mapping Aggregates (Non-abstention examples only)
        non_abstain_records = [r for r in eval_records if not r["should_abstain"]]
        if non_abstain_records:
            top_1_acc = float(np.mean([r["mapping_top1"] for r in non_abstain_records]))
            top_k_acc = float(np.mean([r["mapping_topk"] for r in non_abstain_records]))
            mrr = float(np.mean([r["mapping_mrr"] for r in non_abstain_records]))
        else:
            top_1_acc, top_k_acc, mrr = 0.0, 0.0, 0.0

        # Abstention Aggregates
        abst_evals = [r["abstention_eval"] for r in eval_records]
        abst_summary = aggregate_abstention_metrics(abst_evals)

        # Calibration Metrics (Raw vs Platt Scaled)
        if calibration_scores and len(set(calibration_labels)) >= 1:
            raw_calibration = calculate_ece(calibration_scores, calibration_labels, n_bins=5)
            # Fit Platt Scaler
            scaler = PlattScaler().fit(calibration_scores, calibration_labels)
            calibrated_probs = scaler.predict_proba(calibration_scores)
            post_calibration = calculate_ece(calibrated_probs, calibration_labels, n_bins=5)
        else:
            raw_calibration = {"ece": 0.0, "mce": 0.0, "brier_score": 0.0, "reliability_bins": []}
            post_calibration = {"ece": 0.0, "mce": 0.0, "brier_score": 0.0, "reliability_bins": []}

        # Fairness Audit
        fairness_summary = audit_fairness_slices(eval_records)

        return {
            "dataset_id": self.dataset.dataset_id,
            "version": self.dataset.version,
            "empirical_status": self.dataset.empirical_status,
            "provenance_metadata": self.dataset.metadata,
            "total_examples": total_examples,
            "extraction_metrics": {
                "exact": {
                    "precision": round(mean_exact_prec, 4),
                    "recall": round(mean_exact_rec, 4),
                    "f1": round(mean_exact_f1, 4),
                },
                "relaxed": {
                    "precision": round(mean_rel_prec, 4),
                    "recall": round(mean_rel_rec, 4),
                    "f1": round(mean_rel_f1, 4),
                },
            },
            "mapping_metrics": {
                "top_1_accuracy": round(top_1_acc, 4),
                f"top_{top_k}_accuracy": round(top_k_acc, 4),
                "mrr": round(mrr, 4),
                "evaluated_non_abstain_examples": len(non_abstain_records),
            },
            "abstention_metrics": abst_summary,
            "calibration_metrics": {
                "raw_similarity": {
                    "ece": raw_calibration.get("ece", 0.0),
                    "mce": raw_calibration.get("mce", 0.0),
                    "brier_score": raw_calibration.get("brier_score", 0.0),
                    "reliability_bins": raw_calibration.get("reliability_bins", []),
                },
                "calibrated_platt": {
                    "ece": post_calibration.get("ece", 0.0),
                    "mce": post_calibration.get("mce", 0.0),
                    "brier_score": post_calibration.get("brier_score", 0.0),
                    "reliability_bins": post_calibration.get("reliability_bins", []),
                },
            },
            "fairness_audit": fairness_summary,
            "per_example_results": [
                {
                    "example_id": r["example_id"],
                    "trade": r["trade"],
                    "style": r["style"],
                    "extracted_skills": r["extracted_skills"],
                    "extraction_relaxed_f1": r["extraction_f1"],
                    "mapping_top1": r["mapping_top1"],
                    "mapping_topk": r["mapping_topk"],
                    "abstained": r["predicted_abstained"],
                    "abstention_category": r["abstention_eval"]["category"],
                }
                for r in eval_records
            ],
            "integrity_notice": (
                "Empirical status: " + self.dataset.empirical_status + ". "
                "Synthetic functional benchmark fixtures are pending empirical real-world field evaluation with human assessors."
            ),
        }
