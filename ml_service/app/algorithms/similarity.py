"""
KaushalTwin ML Service — Similarity Algorithms
Module 2: Skill Intelligence & NOS Mapping
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    similarity = dot(A,B) / (||A|| * ||B||)

    Returns 0.0 if either vector is the zero vector.
    """
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_similarity_matrix(
    query_vecs: list[list[float]],
    corpus_vecs: list[list[float]],
) -> list[list[float]]:
    """
    Compute cosine similarities between all query/corpus pairs.
    Returns a (len(query), len(corpus)) matrix.
    """
    Q = np.array(query_vecs, dtype=np.float64)
    C = np.array(corpus_vecs, dtype=np.float64)

    # Normalise rows
    q_norms = np.linalg.norm(Q, axis=1, keepdims=True)
    c_norms = np.linalg.norm(C, axis=1, keepdims=True)
    q_norms[q_norms == 0] = 1.0
    c_norms[c_norms == 0] = 1.0

    Q_norm = Q / q_norms
    C_norm = C / c_norms
    sim = Q_norm @ C_norm.T  # (n_q, n_c)
    return sim.tolist()


# ---------------------------------------------------------------------------
# TF-IDF / lexical similarity
# ---------------------------------------------------------------------------

def _tokenise_simple(text: str) -> list[str]:
    """Lower-case alphabetic tokenisation."""
    return re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower())


def tfidf_vectors(
    query: str,
    corpus: list[str],
) -> tuple[list[float], list[list[float]]]:
    """
    Build TF-IDF vectors for query and corpus documents.
    Returns (query_vector, [corpus_vectors]).
    Simple implementation — no external dependency.
    """
    docs = [query] + corpus
    tokenised = [_tokenise_simple(d) for d in docs]

    # Build vocabulary
    vocab: dict[str, int] = {}
    for toks in tokenised:
        for tok in toks:
            if tok not in vocab:
                vocab[tok] = len(vocab)

    n_docs = len(docs)
    n_terms = len(vocab)

    # Document frequency
    df = Counter[str]()
    for toks in tokenised:
        for tok in set(toks):
            df[tok] += 1

    def tfidf_vec(toks: list[str]) -> list[float]:
        tf = Counter(toks)
        total = len(toks) or 1
        vec = [0.0] * n_terms
        for tok, idx in vocab.items():
            if tf[tok] > 0:
                idf = math.log((n_docs + 1) / (df[tok] + 1)) + 1.0
                vec[idx] = (tf[tok] / total) * idf
        return vec

    vecs = [tfidf_vec(t) for t in tokenised]
    return vecs[0], vecs[1:]


def tfidf_similarity(query: str, candidate: str) -> float:
    """Compute TF-IDF cosine similarity between query and one candidate."""
    q_vec, [c_vec] = tfidf_vectors(query, [candidate])
    return cosine_similarity(q_vec, c_vec)


# ---------------------------------------------------------------------------
# Keyword / lexical overlap
# ---------------------------------------------------------------------------

def keyword_overlap_score(phrase_a: str, phrase_b: str) -> float:
    """
    Jaccard-style keyword overlap between two phrases.
    Ignores very short tokens.
    """
    toks_a = set(t for t in _tokenise_simple(phrase_a) if len(t) > 2)
    toks_b = set(t for t in _tokenise_simple(phrase_b) if len(t) > 2)
    if not toks_a or not toks_b:
        return 0.0
    intersection = len(toks_a & toks_b)
    union = len(toks_a | toks_b)
    return intersection / union


def exact_match_score(phrase_a: str, phrase_b: str) -> float:
    """Return 1.0 if normalised strings are equal, else 0.0."""
    return 1.0 if phrase_a.strip().lower() == phrase_b.strip().lower() else 0.0


# ---------------------------------------------------------------------------
# Hybrid scorer
# ---------------------------------------------------------------------------

class HybridScorer:
    """
    Combines lexical, TF-IDF, and (optionally) embedding similarity.

    Weights are configurable; defaults sum to 1.0.
    All individual scores must be independently computable — no black box.
    """

    def __init__(
        self,
        w_exact: float = 0.35,
        w_keyword: float = 0.25,
        w_tfidf: float = 0.20,
        w_embedding: float = 0.20,
    ) -> None:
        self.w_exact = w_exact
        self.w_keyword = w_keyword
        self.w_tfidf = w_tfidf
        self.w_embedding = w_embedding

    def score(
        self,
        query: str,
        candidate: str,
        embedding_score: Optional[float] = None,
    ) -> dict[str, float]:
        """
        Return a breakdown of similarity signals and the combined score.
        If embedding_score is None, redistribute its weight to TF-IDF.
        """
        exact = exact_match_score(query, candidate)
        keyword = keyword_overlap_score(query, candidate)
        tfidf = tfidf_similarity(query, candidate)

        if embedding_score is None:
            # No embedding available — redistribute weight
            w_total = self.w_exact + self.w_keyword + self.w_tfidf
            we = self.w_exact / w_total
            wk = self.w_keyword / w_total
            wt = self.w_tfidf / w_total
            combined = we * exact + wk * keyword + wt * tfidf
            methods = []
        else:
            combined = (
                self.w_exact * exact
                + self.w_keyword * keyword
                + self.w_tfidf * tfidf
                + self.w_embedding * embedding_score
            )
            methods = ["embedding"]

        if exact > 0:
            methods.append("exact_match")
        if keyword > 0.1:
            methods.append("keyword_overlap")
        if tfidf > 0.1:
            methods.append("tfidf")

        return {
            "exact_score": round(exact, 4),
            "keyword_score": round(keyword, 4),
            "tfidf_score": round(tfidf, 4),
            "embedding_score": round(embedding_score, 4) if embedding_score is not None else None,
            "combined_score": round(min(combined, 1.0), 4),
            "methods": methods,
        }
