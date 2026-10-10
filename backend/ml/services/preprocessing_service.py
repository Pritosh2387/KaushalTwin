"""
KaushalTwin ML Service — Preprocessing Service
Module 1: Data Ingestion & ML Preprocessing
"""

from __future__ import annotations

from ml.utils.normalisation import (
    normalise_text,
    tokenise,
    split_sentences,
    infer_language,
)


def preprocess_text(
    text: str,
    language: str | None = None,
    lowercase: bool = False,
) -> dict:
    """
    Full text preprocessing pipeline.

    Returns both original and normalised text; never destroys source.
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    original_text = text
    normalised = normalise_text(text, lowercase=lowercase)
    detected_language = infer_language(text, declared_language=language)
    tokens = tokenise(normalised)
    sentences = split_sentences(normalised)

    return {
        "original_text": original_text,
        "normalized_text": normalised,
        "language": detected_language,
        "tokens": tokens,
        "sentences": sentences,
        "token_count": len(tokens),
        "sentence_count": len(sentences),
    }
