"""
KaushalTwin ML Service — Text Normalisation Utilities
Module 1: Data Ingestion & ML Preprocessing
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SENTENCE_SPLITTERS = re.compile(r"(?<=[.!?।])\s+")
_MULTI_SPACE = re.compile(r"\s{2,}")
_WHITESPACE_AROUND_PUNCT = re.compile(r"\s+([,;:.!?])")


# ---------------------------------------------------------------------------
# Core normalisation
# ---------------------------------------------------------------------------

def unicode_normalise(text: str) -> str:
    """NFC Unicode normalisation — keeps Devanagari and Latin characters intact."""
    return unicodedata.normalize("NFC", text)


def normalise_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs/newlines into single spaces and strip."""
    text = text.replace("\t", " ").replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def fix_punctuation_spacing(text: str) -> str:
    """Remove space before punctuation (e.g. 'hello , world' → 'hello, world')."""
    return _WHITESPACE_AROUND_PUNCT.sub(r"\1", text)


def normalise_text(text: str, lowercase: bool = False) -> str:
    """
    Full normalisation pipeline.
    Original text is NOT modified here — caller decides whether to keep it.
    """
    text = unicode_normalise(text)
    text = normalise_whitespace(text)
    text = fix_punctuation_spacing(text)
    if lowercase:
        text = text.lower()
    return text


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

def tokenise(text: str) -> list[str]:
    """
    Simple whitespace + punctuation tokeniser.
    Returns lowercase tokens, strips leading/trailing punctuation per token.
    Works on mixed Hindi/English text.
    """
    raw = text.split()
    tokens: list[str] = []
    punct = ".,;:!?।॥\"'()"
    for tok in raw:
        tok = tok.strip(punct).lower()
        if tok:
            tokens.append(tok)
    return tokens


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences on . ! ? and Devanagari full-stop ।
    """
    parts = _SENTENCE_SPLITTERS.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Language helpers
# ---------------------------------------------------------------------------

def contains_devanagari(text: str) -> bool:
    """Return True if the text contains any Devanagari characters."""
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def detect_script(text: str) -> str:
    """
    Heuristic script detection.
    Returns 'devanagari', 'latin', or 'mixed'.
    """
    deva_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    latin_count = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    total = deva_count + latin_count
    if total == 0:
        return "unknown"
    ratio = deva_count / total
    if ratio > 0.7:
        return "devanagari"
    if ratio < 0.3:
        return "latin"
    return "mixed"


def infer_language(text: str, declared_language: Optional[str] = None) -> str:
    """
    Infer a language code.
    If the caller declares a language, trust it.
    Otherwise use script heuristics to distinguish Hindi from English.
    Returns an ISO 639-1 code: 'hi', 'en', or 'mixed'.
    """
    if declared_language:
        return declared_language.lower()
    script = detect_script(text)
    if script == "devanagari":
        return "hi"
    if script == "latin":
        return "en"
    return "mixed"


# ---------------------------------------------------------------------------
# Keyword extraction helper (for later NOS matching)
# ---------------------------------------------------------------------------

_STOP_WORDS_EN = frozenset({
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "must", "can",
    "the", "a", "an", "and", "or", "but", "for", "nor", "so", "yet",
    "at", "by", "in", "of", "on", "to", "up", "as",
    "years", "year", "also", "been", "about", "from", "with",
})

_STOP_WORDS_HI = frozenset({
    "main", "mein", "aur", "hai", "hoon", "karta", "karti",
    "tha", "thi", "se", "ka", "ki", "ke", "ko", "par", "pe",
    "yeh", "wo", "jo", "koi", "kuch", "bhi", "hi", "toh",
    "ne", "ek", "saat", "teen", "do",
})

_STOP_WORDS = _STOP_WORDS_EN | _STOP_WORDS_HI


def extract_keywords(text: str) -> list[str]:
    """
    Extract meaningful keywords from text after tokenisation.
    Removes stop words (basic English + basic Hindi romanised).
    """
    tokens = tokenise(text)
    return [t for t in tokens if len(t) > 2 and t not in _STOP_WORDS]
