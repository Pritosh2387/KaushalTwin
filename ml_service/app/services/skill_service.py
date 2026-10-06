"""
KaushalTwin ML Service — Skill Service
Module 2: Skill Intelligence & NOS Mapping
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.providers.skill_provider import get_skill_extraction_provider
from app.providers.embedding_provider import get_embedding_provider
from app.algorithms.similarity import HybridScorer, cosine_similarity
from app.utils.normalisation import normalise_text

# ---------------------------------------------------------------------------
# NOS repository
# ---------------------------------------------------------------------------

_NOS_PATH = Path(__file__).parent.parent / "data" / "demo_nos.json"
_nos_cache: Optional[list[dict]] = None
_nos_embeddings_cache: Optional[list[list[float]]] = None


def _load_nos() -> list[dict]:
    global _nos_cache
    if _nos_cache is None:
        with open(_NOS_PATH, encoding="utf-8") as f:
            _nos_cache = json.load(f)
    return _nos_cache


def _nos_embedding_corpus(provider_name: str = "demo") -> tuple[list[dict], list[list[float]]]:
    """Return NOS list and their cached embeddings."""
    global _nos_embeddings_cache
    nos_list = _load_nos()
    if _nos_embeddings_cache is None:
        provider = get_embedding_provider(provider_name)
        texts = [
            f"{n['title']} {n['description']} {' '.join(n.get('keywords', []))}"
            for n in nos_list
        ]
        _nos_embeddings_cache = provider.embed_batch(texts)
    return nos_list, _nos_embeddings_cache


# ---------------------------------------------------------------------------
# Skill extraction service
# ---------------------------------------------------------------------------

def extract_skills(
    text: str,
    language: str = "en",
    trade: str = "electrician",
    provider_name: str = "demo",
    api_key: str = "",
) -> dict:
    """Extract skills from a worker transcript."""
    provider = get_skill_extraction_provider(provider_name, api_key=api_key)
    skills = provider.extract_skills(text, language=language, trade=trade)
    return {
        "skills": skills,
        "count": len(skills),
        "provider": provider.provider_name,
        "trade": trade,
        "language": language,
    }


# ---------------------------------------------------------------------------
# NOS mapping service
# ---------------------------------------------------------------------------

def map_skills_to_nos(
    skills: list[dict],
    top_k: int = 3,
    embedding_provider_name: str = "demo",
) -> list[dict]:
    """
    Map each extracted skill to candidate NOS elements.

    Uses hybrid scoring: exact match + keyword overlap + TF-IDF + embedding.
    Returns CANDIDATE mappings only — never certified.
    """
    nos_list, nos_embs = _nos_embedding_corpus(embedding_provider_name)
    emb_provider = get_embedding_provider(embedding_provider_name)
    scorer = HybridScorer()

    results = []
    for skill in skills:
        skill_text = skill.get("normalized_name", skill.get("skill_name", ""))
        skill_emb = emb_provider.embed_text(skill_text)

        candidates = []
        for nos, nos_emb in zip(nos_list, nos_embs):
            nos_text = f"{nos['title']} {' '.join(nos.get('keywords', []))}"
            emb_sim = cosine_similarity(skill_emb, nos_emb)
            scores = scorer.score(skill_text, nos_text, embedding_score=emb_sim)

            candidates.append({
                "nos_id": nos["id"],
                "title": nos["title"],
                "mandatory": nos.get("mandatory", False),
                "weight": nos.get("weight", 0.5),
                "similarity": scores["combined_score"],
                "signals": {
                    "exact_score": scores["exact_score"],
                    "keyword_score": scores["keyword_score"],
                    "tfidf_score": scores["tfidf_score"],
                    "embedding_score": scores["embedding_score"],
                },
                "methods": scores["methods"],
                "source_type": nos.get("source_type", "DEMO"),
                "mapping_status": "SUGGESTED",  # never auto-certified
            })

        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        results.append({
            "skill": skill,
            "candidates": candidates[:top_k],
        })

    return results


def search_nos(query: str, top_k: int = 5, embedding_provider_name: str = "demo") -> list[dict]:
    """Free-text search across the NOS repository."""
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
            "nos_id": nos["id"],
            "title": nos["title"],
            "description": nos["description"],
            "mandatory": nos.get("mandatory", False),
            "similarity": scores["combined_score"],
            "methods": scores["methods"],
            "source_type": nos.get("source_type", "DEMO"),
        })

    results.sort(key=lambda r: r["similarity"], reverse=True)
    return results[:top_k]


def get_all_nos() -> list[dict]:
    """Return the full NOS repository."""
    return _load_nos()


def get_nos_by_id(nos_id: str) -> Optional[dict]:
    """Return a single NOS element by ID."""
    for nos in _load_nos():
        if nos["id"] == nos_id:
            return nos
    return None
