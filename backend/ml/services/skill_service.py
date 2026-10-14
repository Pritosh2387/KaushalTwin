"""
KaushalTwin ML Service — Skill Service
Module 2: Skill Intelligence & NOS Mapping

Priority 5: Extended with:
- Multi-signal NOS mapping (embedding + keyword/performance-criteria overlap + trade compatibility)
- Configurable similarity threshold with explicit abstention when evidence is insufficient
- Ambiguity detection when top candidates are within a configurable margin
- Match reason explanations
- Trade-aware ranking
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List

from ml.providers.skill_provider import get_skill_extraction_provider
from ml.providers.embedding_provider import get_embedding_provider
from ml.algorithms.similarity import HybridScorer, cosine_similarity
from ml.utils.normalisation import normalise_text
from ml.schemas.skills import SkillExtractionResponse, NOSMappingResponse, SkillNOSMapping, NOSCandidate
from ml.services.exceptions import (
    NOSMappingError,
    MLProviderError,
    InvalidInputError,
)
from ml.trade_registry import normalize_skill_via_synonyms, get_all_aliases
from app.core.config import settings

# ---------------------------------------------------------------------------
# NOS repository
# ---------------------------------------------------------------------------

from ml.nos_repository import get_nos_repository

_nos_repository = get_nos_repository()
_nos_embeddings_cache: Optional[list[list[float]]] = None
_last_dataset_hash: Optional[str] = None
_last_dataset_source: Optional[str] = None


def invalidate_nos_cache() -> None:
    """Explicitly invalidate both repository cache and skill service embedding cache."""
    global _nos_embeddings_cache, _last_dataset_hash, _last_dataset_source
    _nos_embeddings_cache = None
    _last_dataset_hash = None
    _last_dataset_source = None
    _nos_repository.clear_cache()


def set_active_nos_dataset(source: Union[str, Path, None] = None) -> Dict[str, Any]:
    """
    Switch the active NOS dataset in the repository and invalidate embedding caches.

    Args:
        source: 'official', 'demo', a specific Path / string path, or None for default

    Returns:
        Dataset information dictionary
    """
    global _nos_embeddings_cache, _last_dataset_hash, _last_dataset_source
    _nos_embeddings_cache = None
    _last_dataset_hash = None
    _last_dataset_source = None

    if source is None or str(source).lower() == "demo":
        _nos_repository.load_demo_data(refresh=True)
    elif str(source).lower() == "official":
        _nos_repository.load_official_data(refresh=True)
    else:
        _nos_repository.load_nos_data(source, refresh=True)

    return _nos_repository.get_dataset_info()


def get_active_nos_dataset_info() -> Dict[str, Any]:
    """Return dataset metadata and status for the currently active NOS repository."""
    return _nos_repository.get_dataset_info()


def _load_nos() -> list[dict]:
    """Load NOS data from the repository."""
    return _nos_repository.get_all_nos()


def _nos_embedding_corpus(provider_name: str = "demo") -> tuple[list[dict], list[list[float]]]:
    """Return NOS list and their cached embeddings, invalidating cache if dataset changed."""
    try:
        global _nos_embeddings_cache, _last_dataset_hash, _last_dataset_source
        nos_list = _load_nos()
        repo_info = _nos_repository.get_dataset_info()
        current_hash = repo_info.get("hash")
        current_source = repo_info.get("source")

        # Automatically invalidate embedding cache if dataset source or content changed
        if (_nos_embeddings_cache is not None and
            (current_source != _last_dataset_source or current_hash != _last_dataset_hash)):
            _nos_embeddings_cache = None

        if _nos_embeddings_cache is None:
            provider = get_embedding_provider(provider_name)
            texts = [
                f"{n['title']} {n['description']} {' '.join(n.get('keywords', []))}"
                for n in nos_list
            ]
            _nos_embeddings_cache = provider.embed_batch(texts)
            _last_dataset_hash = current_hash
            _last_dataset_source = current_source
        return nos_list, _nos_embeddings_cache
    except Exception as exc:
        raise MLProviderError(f"Embedding provider failed: {str(exc)}", provider_name=provider_name) from exc


# ---------------------------------------------------------------------------
# Skill extraction service
# ---------------------------------------------------------------------------

def extract_skills(
    text: str,
    language: str = "en",
    trade: str = "general",
) -> SkillExtractionResponse:
    """Extract skills from a worker transcript."""
    # Use centralized configuration for provider selection
    provider_name = "llm" if settings.SKILL_EXTRACTION_PROVIDER == "llm" and settings.LLM_SKILL_API_KEY else "demo"
    api_key = settings.LLM_SKILL_API_KEY if provider_name == "llm" else ""

    try:
        provider = get_skill_extraction_provider(provider_name, api_key=api_key)
        skills = provider.extract_skills(text, language=language, trade=trade)
        return SkillExtractionResponse(
            skills=skills,
            count=len(skills),
            provider=provider.provider_name,
            trade=trade,
            language=language,
        )
    except Exception as exc:
        raise MLProviderError(
            f"Skill extraction failed: {str(exc)}",
            provider_name=provider_name
        ) from exc


# ---------------------------------------------------------------------------
# NOS mapping helpers — multi-signal scoring
# ---------------------------------------------------------------------------

def _keyword_overlap_with_nos(skill_text: str, nos: dict) -> tuple[float, list[str]]:
    """
    Compute keyword overlap between skill text and a NOS element's keywords list + title.
    Returns (score, matched_keywords).
    """
    nos_keywords = [k.lower() for k in nos.get("keywords", [])]
    skill_lower = skill_text.lower()
    title_lower = nos.get("title", "").lower()

    matched = [kw for kw in nos_keywords if kw in skill_lower]
    skill_words = [w for w in skill_lower.split() if len(w) > 2]
    title_matches = [w for w in skill_words if w in title_lower]

    if not nos_keywords and not skill_words:
        return 0.0, []

    kw_ratio = len(matched) / max(len(nos_keywords), 1)
    title_ratio = len(title_matches) / max(len(skill_words), 1)
    score = min(max(kw_ratio * 1.5, title_ratio), 1.0)

    all_matched = list(set(matched + title_matches))
    return round(score, 4), all_matched


def _performance_criteria_overlap(skill_text: str, nos: dict) -> tuple[float, list[str]]:
    """
    Compute how many performance criteria of the NOS contain keywords from the skill text.
    Returns (score, matched_criteria).
    """
    criteria = nos.get("performance_criteria", [])
    if not criteria:
        return 0.0, []

    skill_tokens = set(
        t for t in skill_text.lower().split()
        if len(t) > 2
    )
    matched = []
    for criterion in criteria:
        crit_lower = criterion.lower()
        if any(tok in crit_lower for tok in skill_tokens):
            matched.append(criterion)

    score = len(matched) / len(criteria)
    return min(score, 1.0), matched


def _trade_compatibility_bonus(skill_trade: Optional[str], nos_trade: Optional[str]) -> tuple[float, bool]:
    """
    Return a bonus/penalty score based on trade compatibility, and a flag.
    Returns (bonus, trade_matches).
    """
    if not skill_trade or not nos_trade:
        return 0.0, False
    skill_trade_lower = skill_trade.lower()
    nos_trade_lower = nos_trade.lower()
    if skill_trade_lower in ("general", "multi-trade") or nos_trade_lower in ("general", "multi-trade"):
        return 0.0, False
    match = skill_trade_lower == nos_trade_lower
    return (0.15 if match else -0.15), match


def _synonym_match_bonus(skill_text: str, nos: dict, trade: str) -> tuple[float, list[str]]:
    """
    Check if any trade synonyms for the NOS's keywords appear in the skill text.
    Returns (bonus, matched_synonyms).
    """
    aliases = get_all_aliases(trade)
    skill_lower = skill_text.lower()
    nos_keywords = [k.lower() for k in nos.get("keywords", [])]
    nos_title_lower = nos.get("title", "").lower()

    matched_via_synonym = []
    for alias, canonical in aliases.items():
        if alias in skill_lower:
            # Does this alias point to something in the NOS keywords or title?
            if canonical.lower() in nos_title_lower or any(canonical.lower() in kw for kw in nos_keywords):
                matched_via_synonym.append(f"{alias} → {canonical}")

    if not matched_via_synonym:
        return 0.0, []
    bonus = min(len(matched_via_synonym) * 0.05, 0.15)
    return bonus, matched_via_synonym


def _build_match_reasons(
    exact_score: float,
    keyword_score: float,
    tfidf_score: float,
    embedding_score: Optional[float],
    kw_matched: list[str],
    pc_matched: list[str],
    trade_matches: bool,
    synonym_matched: list[str],
) -> list[str]:
    """Build human-readable match reason strings."""
    reasons = []
    if exact_score > 0:
        reasons.append("Exact skill name match")
    if kw_matched:
        reasons.append(f"Matched NOS keywords: {', '.join(kw_matched[:3])}")
    if pc_matched:
        reasons.append(f"Matched {len(pc_matched)} performance criteria")
    if tfidf_score > 0.2:
        reasons.append(f"Lexical similarity (TF-IDF: {tfidf_score:.2f})")
    if embedding_score is not None and embedding_score > 0.3:
        reasons.append(f"Semantic similarity (embedding: {embedding_score:.2f})")
    if trade_matches:
        reasons.append("Trade domain match")
    if synonym_matched:
        reasons.append(f"Synonym matches: {', '.join(synonym_matched[:2])}")
    if not reasons:
        reasons.append("Partial lexical overlap")
    return reasons


# ---------------------------------------------------------------------------
# NOS mapping service
# ---------------------------------------------------------------------------

def map_skills_to_nos(
    skills: list[dict],
    top_k: int = 3,
    min_similarity_threshold: float = 0.0,
    ambiguity_margin: float = 0.05,
) -> List[dict]:
    """
    Map each extracted skill to candidate NOS elements.

    Uses multi-signal hybrid scoring:
    - Embedding cosine similarity
    - Keyword overlap with NOS keyword list
    - Performance criteria overlap
    - TF-IDF lexical similarity
    - Trade compatibility bonus
    - Synonym match bonus

    Applies configurable threshold: if all candidates score below
    min_similarity_threshold, the mapping is marked as abstained.

    Detects ambiguity: if top-2 candidates are within ambiguity_margin,
    the mapping is flagged.

    Returns CANDIDATE mappings only — never certified.
    """
    embedding_provider_name = "sentence_transformer" if settings.EMBEDDING_PROVIDER == "sentence_transformer" else "demo"

    try:
        nos_list, nos_embs = _nos_embedding_corpus(embedding_provider_name)
        emb_provider = get_embedding_provider(embedding_provider_name)
        scorer = HybridScorer()

        results = []
        for skill in skills:
            skill_text = skill.get("normalized_name", skill.get("skill_name", ""))
            skill_trade = skill.get("trade_context", "general")
            skill_emb = emb_provider.embed_text(skill_text)

            candidates = []
            for nos, nos_emb in zip(nos_list, nos_embs):
                nos_text = f"{nos['title']} {' '.join(nos.get('keywords', []))}"
                emb_sim = cosine_similarity(skill_emb, nos_emb)
                scores = scorer.score(skill_text, nos_text, embedding_score=emb_sim)

                # Additional multi-signal scoring (Priority 5)
                kw_score, kw_matched = _keyword_overlap_with_nos(skill_text, nos)
                pc_score, pc_matched = _performance_criteria_overlap(skill_text, nos)
                trade_bonus, trade_matches = _trade_compatibility_bonus(skill_trade, nos.get("trade"))
                syn_bonus, syn_matched = _synonym_match_bonus(skill_text, nos, skill_trade or "general")

                # Weighted combination of all signals
                # Base combined score from HybridScorer
                base_score = scores["combined_score"]
                # Augment with additional signals
                augmented_score = (
                    base_score * 0.45
                    + kw_score * 0.25
                    + pc_score * 0.10
                    + trade_bonus * 0.15
                    + syn_bonus * 0.05
                )
                final_score = max(0.0, min(augmented_score, 1.0))

                match_reasons = _build_match_reasons(
                    exact_score=scores["exact_score"],
                    keyword_score=scores["keyword_score"],
                    tfidf_score=scores["tfidf_score"],
                    embedding_score=scores["embedding_score"],
                    kw_matched=kw_matched,
                    pc_matched=pc_matched,
                    trade_matches=trade_matches,
                    synonym_matched=syn_matched,
                )

                # Get NOS ID with fallback to support different field names
                nos_id = nos.get("nos_id") or nos.get("id") or nos.get("code") or f"unknown_{id(nos)}"

                candidates.append({
                    "nos_id": nos_id,
                    "title": nos["title"],
                    "mandatory": nos.get("mandatory", False),
                    "weight": nos.get("weight", 0.5),
                    "similarity": round(final_score, 4),
                    "signals": {
                        "exact_score": scores["exact_score"],
                        "keyword_score": scores["keyword_score"],
                        "tfidf_score": scores["tfidf_score"],
                        "embedding_score": scores["embedding_score"],
                        "nos_keyword_overlap": round(kw_score, 4),
                        "performance_criteria_overlap": round(pc_score, 4),
                        "trade_bonus": round(trade_bonus, 4),
                        "synonym_bonus": round(syn_bonus, 4),
                    },
                    "methods": scores["methods"],
                    "source_type": nos.get("source_type", "DEMO"),
                    "mapping_status": "SUGGESTED",  # never auto-certified
                    # Preserve provenance information for traceability
                    "provenance": {
                        k: nos.get(k) for k in [
                            "source_name", "source_url", "source_version",
                            "source_published_at", "retrieved_at", "imported_at", "content_hash"
                        ] if nos.get(k) is not None
                    },
                    # Priority 5 additions
                    "match_reasons": match_reasons,
                    "trade_match": trade_matches,
                    "ambiguity_flag": False,  # set below
                })

            candidates.sort(key=lambda c: c["similarity"], reverse=True)

            # Apply threshold: abstain if no candidate meets the minimum
            above_threshold = [c for c in candidates if c["similarity"] >= min_similarity_threshold]

            if min_similarity_threshold > 0 and not above_threshold:
                # Abstain — no confident match
                results.append({
                    "skill": skill,
                    "candidates": [],
                    "abstained": True,
                    "abstention_reason": (
                        f"No NOS candidate scored at or above the minimum similarity threshold "
                        f"({min_similarity_threshold:.2f}). "
                        f"Best score: {candidates[0]['similarity']:.4f} for '{candidates[0]['title']}'. "
                        "Insufficient evidence for a confident match."
                    ),
                })
                continue

            # Use above-threshold candidates (or all if no threshold)
            final_candidates = above_threshold if min_similarity_threshold > 0 else candidates
            top_candidates = final_candidates[:top_k]

            # Mark ambiguity when top-2 candidates are within the margin
            if len(top_candidates) >= 2:
                top_sim = top_candidates[0]["similarity"]
                second_sim = top_candidates[1]["similarity"]
                if (top_sim - second_sim) <= ambiguity_margin:
                    top_candidates[0]["ambiguity_flag"] = True
                    top_candidates[1]["ambiguity_flag"] = True

            results.append({
                "skill": skill,
                "candidates": top_candidates,
                "abstained": False,
                "abstention_reason": None,
            })

        return results
    except FileNotFoundError as exc:
        raise NOSMappingError(f"NOS data file not found: {str(exc)}") from exc
    except json.JSONDecodeError as exc:
        raise NOSMappingError(f"Invalid NOS data format: {str(exc)}") from exc
    except Exception as exc:
        raise NOSMappingError(f"NOS mapping failed: {str(exc)}") from exc


def search_nos(query: str, top_k: int = 5) -> List[dict]:
    """Free-text search across the NOS repository."""
    # Use centralized configuration for embedding provider selection
    embedding_provider_name = "sentence_transformer" if settings.EMBEDDING_PROVIDER == "sentence_transformer" else "demo"

    try:
        nos_list, nos_embs = _nos_embedding_corpus(embedding_provider_name)
        emb_provider = get_embedding_provider(embedding_provider_name)
        scorer = HybridScorer()

        query_norm = normalise_text(query, lowercase=True)
        query_emb = emb_provider.embed_text(query_norm)

        results = []
        for nos, nos_emb in zip(nos_list, nos_embs):
            nos_text = f"{nos['title']} {nos['description']} {' '.join(nos.get('keywords', []))}"
            emb_sim = cosine_similarity(query_emb, nos_emb)
            scores = scorer.score(query_norm, nos_text, embedding_score=emb_sim)

            results.append({
                # Get NOS ID with fallback to support different field names
                "nos_id": nos.get("nos_id") or nos.get("id") or nos.get("code") or f"unknown_{id(nos)}",
                "title": nos["title"],
                "description": nos["description"],
                "mandatory": nos.get("mandatory", False),
                "similarity": scores["combined_score"],
                "methods": scores["methods"],
                "source_type": nos.get("source_type", "DEMO"),
                # Include provenance information for traceability
                "provenance": {
                    k: nos.get(k) for k in [
                        "source_name", "source_url", "source_version",
                        "source_published_at", "retrieved_at", "imported_at", "content_hash"
                    ] if nos.get(k) is not None
                }
            })

        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:top_k]
    except FileNotFoundError as exc:
        raise NOSMappingError(f"NOS data file not found: {str(exc)}") from exc
    except json.JSONDecodeError as exc:
        raise NOSMappingError(f"Invalid NOS data format: {str(exc)}") from exc
    except Exception as exc:
        raise NOSMappingError(f"NOS search failed: {str(exc)}") from exc


def get_all_nos() -> list[dict]:
    """Return the full NOS repository."""
    try:
        return _load_nos()
    except FileNotFoundError as exc:
        raise NOSMappingError(f"NOS data file not found: {str(exc)}") from exc
    except json.JSONDecodeError as exc:
        raise NOSMappingError(f"Invalid NOS data format: {str(exc)}") from exc


def get_nos_by_id(nos_id: str) -> Optional[dict]:
    """Return a single NOS element by ID."""
    try:
        for nos in _load_nos():
            # Check multiple possible ID fields for backward compatibility
            if nos.get("nos_id") == nos_id or nos.get("id") == nos_id or nos.get("code") == nos_id:
                return nos
        return None
    except FileNotFoundError as exc:
        raise NOSMappingError(f"NOS data file not found: {str(exc)}") from exc
    except json.JSONDecodeError as exc:
        raise NOSMappingError(f"Invalid NOS data format: {str(exc)}") from exc
