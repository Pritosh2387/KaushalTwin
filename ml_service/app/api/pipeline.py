"""
KaushalTwin ML Service — Unified Pipeline API
Unified pipeline integrating all 10 modules: transcript → preprocess → skills → NOS → competency → evidence → skill gap → abstention → calibration → certification → explainability → decision report
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.preprocessing_service import preprocess_text
from app.services.skill_service import extract_skills, map_skills_to_nos
from app.services.competency_service import build_competency_twin
from app.services.evidence_service import analyse_evidence
from app.services.task_selection_service import get_next_task, rank_all_tasks
from app.algorithms.task_selector import should_continue_assessment
from app.services.skill_gap_service import SkillGapService
from app.services.abstention_service import AbstentionService
from app.services.calibration_service import CalibrationService
from app.services.certification_service import CertificationService
from app.services.explainability_service import ExplainabilityService


router = APIRouter(prefix="/pipeline", tags=["Unified Pipeline"])


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class PipelineRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)
    language: str = Field("en")
    trade: str = Field("electrician")
    transcript: str = Field(..., min_length=1)
    competencies: list[dict] = Field(
        default=[],
        description="Existing competency state (list of NOSCompetencyInput dicts). Leave empty for first run.",
    )
    evidence: list[dict] = Field(
        default=[],
        description="Evidence records for conflict analysis. Leave empty if none.",
    )
    available_tasks: Optional[list[dict]] = Field(
        None,
        description="Custom task list. If omitted, uses built-in demo tasks.",
    )
    exclude_task_ids: Optional[list[str]] = None
    top_k_nos: int = Field(3, ge=1, le=10)
    # Optional fields for extended pipeline
    assessor_scores: Optional[list[dict]] = Field(
        None,
        description="Assessor scores for calibration (optional).",
    )
    claim: Optional[str] = Field(
        None,
        description="Claim to explain (optional). If not provided, explainability is skipped.",
    )


class PipelineResponse(BaseModel):
    worker_id: str
    preprocessing: dict
    skills: list[dict]
    nos_candidates: list[dict]
    competency_twin: dict
    evidence_features: Optional[dict]
    next_task: Optional[dict]
    ranked_tasks: list[dict]
    continuation: dict
    # Extended pipeline fields (added for Modules 6-10)
    skill_gap_analysis: Optional[dict] = None
    abstention_decision: Optional[dict] = None
    calibration_result: Optional[dict] = None
    certification_recommendation: Optional[dict] = None
    explainability: Optional[dict] = None
    audit_event: Optional[dict] = None
    decision_report: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/worker-assessment",
    response_model=PipelineResponse,
    summary="Run the full ML pipeline for a worker assessment session",
)
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    """
    Unified pipeline integrating all 10 modules:
    1. Preprocess transcript
    2. Extract skills from text
    3. Map skills to NOS candidates
    4. Build competency twin from evidence
    5. Analyse evidence features and integrity
    6. Calculate skill gaps and evidence debt
    7. Check evidence sufficiency and generate abstention recommendation
    8. Assessor calibration and consistency analysis (if assessor scores provided)
    9. Generate competency profile and certification recommendation
    10. Provide explainability, audit trail, and decision report

    All steps are individually callable via their own endpoints.
    This endpoint combines them for demo and integration testing.
    """
    try:
        # Step 1: Preprocess
        pre = preprocess_text(request.transcript, language=request.language)

        # Step 2: Extract skills
        skill_result = extract_skills(
            text=pre["normalized_text"],
            language=pre["language"],
            trade=request.trade,
            provider_name="demo",
        )
        skills = skill_result["skills"]

        # Step 3: Map skills to NOS candidates
        nos_mappings = map_skills_to_nos(skills, top_k=request.top_k_nos)

        # Step 4: Build competency twin (uses provided criteria if any)
        if request.competencies:
            # Check if the competencies are already scored (have competency_score)
            if request.competencies and "competency_score" in request.competencies[0]:
                # Use the provided competencies directly, but ensure they have the required fields for the twin
                competencies = []
                for comp in request.competencies:
                    # Make a copy and add missing fields if needed
                    new_comp = comp.copy()
                    # Ensure we have the fields expected by the rest of the pipeline
                    if "scoring_detail" not in new_comp:
                        new_comp["scoring_detail"] = {
                            "raw_score": new_comp.get("competency_score", 0),
                            "total_weight": 5.0,  # dummy value
                            "observed_count": 0,
                            "max_possible": 5.0,
                        }
                    if "status" not in new_comp:
                        # We can derive status from competency_score and evidence_confidence/coverage, but we'll leave it as is or set to UNASSESSED?
                        # For simplicity, we'll set to UNASSESSED if not present.
                        new_comp["status"] = new_comp.get("status", "UNASSESSED")
                    competencies.append(new_comp)
                # Compute summary
                mandatory_states = [c for c in competencies if c.get("mandatory", False)]
                all_assessed = all(c.get("status") != "UNASSESSED" for c in mandatory_states)
                overall_coverage = (
                    round(
                        sum(c.get("evidence_coverage", 0.0) for c in mandatory_states) / len(mandatory_states),
                        4,
                    )
                    if mandatory_states
                    else 0.0
                )
                twin = {
                    "worker_id": request.worker_id,
                    "competencies": competencies,
                    "summary": {
                        "total_nos": len(competencies),
                        "mandatory_nos": len(mandatory_states),
                        "all_mandatory_assessed": all_assessed,
                        "mandatory_coverage_mean": overall_coverage,
                    },
                }
            else:
                twin = build_competency_twin(request.worker_id, request.competencies)
        else:
            twin = {"worker_id": request.worker_id, "competencies": [], "summary": {}}

        # Step 5: Evidence features (if provided)
        ev_features = None
        if request.evidence:
            ev_features = analyse_evidence(request.evidence)

        # Step 6: Task selection
        competency_states = twin.get("competencies", [])
        next_task = get_next_task(
            competency_states,
            available_tasks=request.available_tasks,
            exclude_task_ids=request.exclude_task_ids,
        )
        ranked = rank_all_tasks(
            competency_states,
            available_tasks=request.available_tasks,
            exclude_task_ids=request.exclude_task_ids,
        )

        # Step 7: Continuation check
        continuation = should_continue_assessment(competency_states)

        # ---------------------------------------------------------------------------
        # Extended Pipeline (Modules 6-10)
        # ---------------------------------------------------------------------------

        # Step 8: Skill Gap Analysis (Module 6)
        skill_gap_result = None
        if request.competencies and request.evidence:
            # The competency_twin already contains the competency profile we need
            competency_profile = twin.get("competencies", [])
            skill_gap_result = SkillGapService.analyze_skill_gaps(
                worker_id=request.worker_id,
                competencies=competency_profile,
                evidence_records=request.evidence,
            )

        # Step 9: Abstention / Evidence Sufficiency (Module 7)
        abstention_result = None
        if request.competencies and request.evidence:
            competency_profile = twin.get("competencies", [])
            abstention_result = AbstentionService.check_evidence_sufficiency(
                worker_id=request.worker_id,
                competencies=competency_profile,
                evidence_records=request.evidence,
                # assessment_task_results and assessor_observations are optional and not provided
            )

        # Step 10: Calibration (Module 8) - only if assessor_scores supplied
        calibration_result = None
        if request.assessor_scores:
            calibration_result = CalibrationService.calculate_assessor_calibration(
                assessor_scores=request.assessor_scores,
                # competency_areas can be derived from nos_mappings if needed, but optional
            )

        # Step 11: Certification Recommendation (Module 9)
        certification_result = None
        if request.competencies:
            competency_profile = twin.get("competencies", [])
            certification_result = CertificationService.make_certification_recommendation(
                worker_id=request.worker_id,
                competency_profile=competency_profile,
                skill_gap_analysis=skill_gap_result,
                abstention_decision=abstention_result,
                calibration_info=calibration_result,
            )

        # Step 12: Explainability (Module 10) - only if claim provided
        explainability_result = None
        if request.claim:
            # We need to map evidence records to the provenance types expected by explainability.
            # For simplicity, we'll treat all evidence as observed_evidence.
            # In a real system, we would categorize evidence by provenance.
            observed_evidence = request.evidence if request.evidence else None
            explainability_result = ExplainabilityService.explain_claim(
                claim=request.claim,
                worker_declaration=None,  # Not available in pipeline
                observed_evidence=observed_evidence,
                assessed_evidence=None,   # Not available
                inferred_evidence=None,   # Not available
                derived_evidence=None,    # Not available
            )

        # Step 13: Generate Audit Event (Module 10)
        audit_event_result = None
        # We create an audit event for the pipeline run itself
        audit_event_result = ExplainabilityService.generate_audit_event(
            worker_id=request.worker_id,
            action="worker_assessment",
            module="pipeline",
            input_summary={
                "transcript": request.transcript[:100] + "..." if len(request.transcript) > 100 else request.transcript,
                "language": request.language,
                "trade": request.trade,
                "competencies_provided": len(request.competencies),
                "evidence_provided": len(request.evidence),
                "available_tasks_provided": request.available_tasks is not None,
            },
            output_summary={
                "skills_extracted": len(skills),
                "nos_mapped": len(nos_mappings),
                "competency_twin built": len(twin.get("competencies", [])),
                "next_task_selected": next_task is not None,
                "skill_gap_completed": skill_gap_result is not None,
                "abstention_checked": abstention_result is not None,
                "calibration_completed": calibration_result is not None,
                "certification_recommendation_generated": certification_result is not None,
                "explainability_completed": explainability_result is not None,
            },
            assessor_id=None,  # Not available in pipeline
            previous_state=None,
            new_state=None,
            evidence_references=[str(i) for i in range(len(request.evidence))] if request.evidence else None,
            model_info={
                "pipeline_version": "1.0",
                "modules_included": ["preprocessing", "skills", "nos_mapping", "competency", "evidence_analysis", "task_selection", "continuation", "skill_gap", "abstention", "calibration", "certification", "explainability", "audit", "decision_report"]
            },
        )

        # Step 14: Generate Decision Report (Module 10)
        decision_report_result = None
        # We need to gather all the required inputs for the decision report
        worker_info = {
            "worker_id": request.worker_id,
            "language": request.language,
            "trade": request.trade,
        }
        skills_extracted = skills
        nos_mapping = nos_mappings
        competency_profile = twin.get("competencies", [])
        evidence_summary = ev_features if ev_features else {}
        skill_gaps = skill_gap_result.get("gaps", []) if skill_gap_result else []
        assessment_summary = {
            "next_task": next_task,
            "ranked_tasks": ranked[:5],  # top 5
            "continuation": continuation,
        }
        abstention_result_for_report = abstention_result if abstention_result else {}
        calibration_info_for_report = calibration_result if calibration_result else None
        certification_recommendation_for_report = certification_result if certification_result else None
        explanation_for_report = explainability_result if explainability_result else None
        audit_event_for_report = audit_event_result if audit_event_result else None

        decision_report_result = ExplainabilityService.generate_decision_report(
            worker_id=request.worker_id,
            worker_info=worker_info,
            skills_extracted=skills_extracted,
            nos_mapping=nos_mapping,
            competency_profile=competency_profile,
            evidence_summary=evidence_summary,
            skill_gaps=skill_gaps,
            assessment_summary=assessment_summary,
            abstention_result=abstention_result_for_report,
            calibration_info=calibration_info_for_report,
            certification_recommendation=certification_recommendation_for_report,
            explanation=explanation_for_report,
            audit_event=audit_event_for_report,
        )

        return PipelineResponse(
            worker_id=request.worker_id,
            preprocessing=pre,
            skills=skills,
            nos_candidates=nos_mappings,
            competency_twin=twin,
            evidence_features=ev_features,
            next_task=next_task,
            ranked_tasks=ranked[:5],  # top 5
            continuation=continuation,
            skill_gap_analysis=skill_gap_result,
            abstention_decision=abstention_result,
            calibration_result=calibration_result,
            certification_recommendation=certification_result,
            explainability=explainability_result,
            audit_event=audit_event_result,
            decision_report=decision_report_result,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "PIPELINE_ERROR", "message": str(exc)}},
        ) from exc