"""
KaushalTwin ML Service — Embedding Provider Interface & Implementations
Module 2: Skill Intelligence & NOS Mapping
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from functools import lru_cache
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class EmbeddingProvider(ABC):
    """
    Abstract embedding provider.
    Implementations must be replaceable without changing business logic.
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Return a float vector embedding for the given text."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a batch of texts."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return a human-readable model identifier."""
        ...

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return len(self.embed_text("test"))


# ---------------------------------------------------------------------------
# Demo TF-IDF-based embedding provider
# ---------------------------------------------------------------------------

class DemoEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic TF-IDF + character-n-gram embedding provider.

    Works without any external models or API keys.
    Produces real vector embeddings — not random numbers.
    Suitable for demo and test runs.
    """

    _VOCAB_SEED = [
        # Cross-trade / General vocabulary
        "safety", "ppe", "regulation", "inspection", "measurement", "testing",
        "plan", "prepare", "drawing", "diagram", "permit", "procedure",
        "install", "connect", "terminate", "route", "protect", "verify",
        "record", "report", "label", "identify", "select", "operate",
        "repair", "maintenance", "troubleshoot", "fault", "diagnosis",
        "domestic", "commercial", "industrial", "quality", "hazard",

        # Electrical trade vocabulary
        "wiring", "switch", "fan", "electrical", "circuit", "multimeter",
        "tester", "voltage", "current", "resistance", "earth", "earthing",
        "conduit", "cable", "mcb", "db", "distribution", "board", "isolation",
        "lockout", "socket", "outlet", "light", "fixture", "relay",
        "capacitor", "insulation", "continuity", "bonding", "power",

        # Plumbing trade vocabulary
        "pipe", "pipes", "pipework", "piping", "plumbing", "water", "supply",
        "drainage", "drain", "sewer", "sewage", "sanitation", "sanitary",
        "toilet", "wc", "commode", "cistern", "flush", "wash", "basin",
        "sink", "shower", "bath", "geyser", "tank", "leak", "leaking",
        "leakage", "seepage", "blockage", "clogged", "trap", "valve",
        "tap", "faucet", "fitting", "joint", "copper", "cpvc", "pvc",
        "upvc", "soldering", "compression",

        # Welding trade vocabulary
        "welding", "welder", "weld", "welds", "arc", "electrode", "rod",
        "mig", "mag", "tig", "smaw", "gmaw", "mma", "stick", "bead",
        "joint", "bevel", "bevelling", "groove", "butt", "fillet",
        "fusion", "shielding", "gas", "argon", "co2", "defect", "porosity",
        "undercut", "crack", "spatter", "slag", "helmet", "mask", "torch",
        "cutting", "grinding", "amperage", "polarity",

        # Masonry trade vocabulary
        "brick", "bricks", "bricklaying", "block", "blocks", "blockwork",
        "mortar", "cement", "sand", "plaster", "plastering", "render",
        "rendering", "wall", "course", "bond", "plumb", "level", "trowel",
        "scaffold", "scaffolding", "concrete", "rcc", "shuttering", "tile",
        "tiles", "tiling", "masonry", "mason", "mix", "mixing",
    ]

    def __init__(self, dim: int = 64) -> None:
        self._dim = dim
        self._vocab = self._build_vocab()

    def _build_vocab(self) -> dict[str, int]:
        vocab: dict[str, int] = {}
        for term in self._VOCAB_SEED:
            for tok in self._tokenise(term):
                if tok not in vocab:
                    vocab[tok] = len(vocab)
            # Add bigrams
            parts = term.split()
            for i in range(len(parts) - 1):
                bg = f"{parts[i]}_{parts[i+1]}"
                if bg not in vocab:
                    vocab[bg] = len(vocab)
        return vocab

    @staticmethod
    def _tokenise(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower())

    def _text_to_vec(self, text: str) -> np.ndarray:
        tokens = self._tokenise(text)
        # Add bigrams
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        all_terms = tokens + bigrams

        tf = Counter(all_terms)
        total = len(all_terms) or 1

        # Fixed-length vector mapped by vocab
        vec = np.zeros(self._dim, dtype=np.float64)
        for term, count in tf.items():
            if term in self._vocab:
                idx = self._vocab[term] % self._dim
                vec[idx] += count / total

        # Deterministic hashing for OOV terms (independent of process hash seed)
        for term in all_terms:
            if term not in self._vocab:
                h = int(hashlib.md5(term.encode("utf-8")).hexdigest(), 16) % self._dim
                vec[h] += 0.1 / total

        # L2 normalise
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def embed_text(self, text: str) -> list[float]:
        return self._text_to_vec(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    @property
    def model_name(self) -> str:
        return "demo-tfidf-embedding-v1"

    @property
    def dimension(self) -> int:
        return self._dim


# ---------------------------------------------------------------------------
# SentenceTransformer provider (optional — requires package)
# ---------------------------------------------------------------------------

class SentenceTransformerProvider(EmbeddingProvider):
    """
    Embedding provider using sentence-transformers.
    Falls back to DemoEmbeddingProvider if the package is unavailable.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model = None
        self._fallback: Optional[DemoEmbeddingProvider] = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        except ImportError:
            self._fallback = DemoEmbeddingProvider()

    def embed_text(self, text: str) -> list[float]:
        if self._model is None:
            return self._fallback.embed_text(text)  # type: ignore[union-attr]
        return self._model.encode(text, show_progress_bar=False).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            return self._fallback.embed_batch(texts)  # type: ignore[union-attr]
        return self._model.encode(texts, show_progress_bar=False).tolist()

    @property
    def model_name(self) -> str:
        if self._model is None:
            return f"fallback-to-{self._fallback.model_name}"  # type: ignore[union-attr]
        return self._model_name


# ---------------------------------------------------------------------------
# Singleton provider factory
# ---------------------------------------------------------------------------

_provider_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider(
    provider_name: str = "demo",
    model_name: str = "all-MiniLM-L6-v2",
) -> EmbeddingProvider:
    """
    Return a singleton embedding provider.
    Model is loaded once and cached.
    """
    global _provider_instance
    if _provider_instance is None:
        if provider_name == "sentence_transformer":
            _provider_instance = SentenceTransformerProvider(model_name)
        else:
            _provider_instance = DemoEmbeddingProvider()
    return _provider_instance
