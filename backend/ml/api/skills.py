"""
KaushalTwin ML Service — Skills & NOS Mapping API
Module 2: Skill Intelligence & NOS Mapping
"""

from fastapi import APIRouter, HTTPException
from ml.schemas.skills import (
    SkillExtractionRequest,
    SkillExtractionResponse,
    NOSMappingRequest,
    NOSMappingResponse,
    NOSSearchRequest,
    NOSSearchResponse,
    ExtractedSkill,
    SkillNOSMapping,
    NOSCandidate,
    NOSSearchResult,
)
from ml.services.skill_service import (
    extract_skills,
    map_skills_to_nos,
    search_nos,
    get_all_nos,
    get_nos_by_id,
)

router = APIRouter(tags=["Module 2 · Skills & NOS Mapping"])

# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

@router.post(
    "/skills/extract",
    response_model=SkillExtractionResponse,
    summary="Extract structured skills from a worker transcript",
)
def extract_skills_endpoint(request: SkillExtractionRequest) -> SkillExtractionResponse:
    """
    Extract structured skills from a raw worker transcript.

    - Works in DEMO MODE with no API keys.
    - Confidence values are deterministic (not random).
    - Supports Hindi, English, and Hinglish input.
    """
    try:
        result = extract_skills(
            text=request.text,
            language=request.language,
            trade=request.trade,
            provider_name=request.provider,
        )
        return SkillExtractionResponse(
            skills=[ExtractedSkill(**s) for s in result["skills"]],
            count=result["count"],
            provider=result["provider"],
            trade=result["trade"],
            language=result["language"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EXTRACTION_ERROR", "message": str(exc)}},
        ) from exc


# ---------------------------------------------------------------------------
# NOS mapping
# ---------------------------------------------------------------------------

@router.post(
    "/nos/map",
    response_model=NOSMappingResponse,
    summary="Map extracted skills to candidate NOS elements",
)
def map_nos_endpoint(request: NOSMappingRequest) -> NOSMappingResponse:
    """
    Map extracted skills to candidate NOS elements using hybrid scoring.

    Returns CANDIDATE MAPPINGS ONLY — never auto-certified.
    Human assessor confirmation is required before use in assessment.
    """
    try:
        skills_raw = [s.model_dump() for s in request.skills]
        mappings = map_skills_to_nos(
            skills=skills_raw,
            top_k=request.top_k,
            embedding_provider_name=request.embedding_provider,
        )
        parsed = []
        for m in mappings:
            parsed.append(SkillNOSMapping(
                skill=ExtractedSkill(**m["skill"]),
                candidates=[NOSCandidate(**c) for c in m["candidates"]],
            ))
        return NOSMappingResponse(mappings=parsed)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "MAPPING_ERROR", "message": str(exc)}},
        ) from exc


# ---------------------------------------------------------------------------
# NOS search
# ---------------------------------------------------------------------------

@router.post(
    "/nos/search",
    response_model=NOSSearchResponse,
    summary="Free-text search across the NOS repository",
)
def search_nos_endpoint(request: NOSSearchRequest) -> NOSSearchResponse:
    results = search_nos(
        query=request.query,
        top_k=request.top_k,
        embedding_provider_name=request.embedding_provider,
    )
    return NOSSearchResponse(
        results=[NOSSearchResult(**r) for r in results],
        query=request.query,
        count=len(results),
    )


# ---------------------------------------------------------------------------
# NOS repository read
# ---------------------------------------------------------------------------

@router.get("/nos", summary="List all NOS elements")
def list_nos():
    return {"nos_elements": get_all_nos(), "count": len(get_all_nos())}


@router.get("/nos/{nos_id}", summary="Get a single NOS element by ID")
def get_nos(nos_id: str):
    nos = get_nos_by_id(nos_id)
    if nos is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"NOS '{nos_id}' not found"}},
        )
    return nos
