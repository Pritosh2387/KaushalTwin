"""
KaushalTwin ML Service — Skill Extraction Provider Interface & Implementations
Module 2: Skill Intelligence & NOS Mapping
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.utils.normalisation import normalise_text, tokenise, extract_keywords

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

SKILLS_OUTPUT = list[dict]  # list of skill dicts


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class SkillExtractionProvider(ABC):
    """
    Abstract interface for skill extraction.
    Implementations are swappable without changing calling code.
    """

    @abstractmethod
    def extract_skills(
        self,
        text: str,
        language: str = "en",
        trade: str = "electrician",
    ) -> SKILLS_OUTPUT:
        """
        Extract structured skills from the given text.

        Returns a list of skill dicts:
            skill_name       : str
            normalized_name  : str
            evidence_text    : str
            confidence       : float  — deterministic in demo mode
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


# ---------------------------------------------------------------------------
# Glossary loader
# ---------------------------------------------------------------------------

_GLOSSARY_PATH = Path(__file__).parent.parent / "data" / "demo_glossary.json"
_glossary_cache: Optional[dict] = None


def _load_glossary() -> dict:
    global _glossary_cache
    if _glossary_cache is None:
        with open(_GLOSSARY_PATH, encoding="utf-8") as f:
            _glossary_cache = json.load(f)
    return _glossary_cache


def normalise_with_glossary(phrase: str, trade: str = "electrician") -> str:
    """
    Attempt to normalise a raw phrase via the trade glossary.
    Returns the normalized_term if found, otherwise the lowercase phrase.
    """
    glossary = _load_glossary()
    phrase_lower = phrase.strip().lower()
    for entry in glossary.get("terms", []):
        candidates = [entry["local_term"].lower()] + [
            a.lower() for a in entry.get("aliases", [])
        ]
        if phrase_lower in candidates:
            return entry["normalized_term"]
    return phrase_lower


# ---------------------------------------------------------------------------
# Demo Skill Extraction Provider
# ---------------------------------------------------------------------------

# Deterministic skill patterns for the electrician trade.
# Each entry: (regex_pattern, skill_name, confidence)
# Confidence is derived from specificity of the match — not random.
_ELECTRICIAN_PATTERNS: list[tuple[str, str, float]] = [
    # Wiring
    (r"\b(house\s+wiring|domestic\s+wiring|ghar\s+ki\s+wiring|internal\s+wiring)\b", "house wiring", 0.93),
    (r"\b(wiring|wire)\b", "electrical wiring", 0.82),
    (r"\b(conduit|pipe\s+mein\s+wire)\b", "conduit installation", 0.80),
    # Switches and fixtures
    (r"\b(switch\s+install|install\s+switch|switch\s+lagana|switch\s+fit)\b", "switch installation", 0.92),
    (r"\b(switch)\b", "switch installation", 0.78),
    (r"\b(fan\s+install|install\s+fan|ceiling\s+fan|pankha\s+lagana|fan\s+fit)\b", "fan installation", 0.91),
    (r"\b(fan)\b", "fan installation", 0.76),
    (r"\b(light\s+point|light\s+install|light\s+fixture)\b", "light fixture installation", 0.85),
    (r"\b(socket|outlet|plug\s+point|power\s+point|point\s+lagana)\b", "socket outlet installation", 0.84),
    # Fault finding
    (r"\b(fault\s+find|fault\s+diagnos|fault\s+dhundh|troubleshoot|fault\s+nikalna|bijli\s+ki\s+garbari)\b", "electrical fault diagnosis", 0.92),
    (r"\b(fault)\b", "electrical fault diagnosis", 0.72),
    # Testing / instruments
    (r"\b(line\s+tester|voltage\s+tester|phase\s+tester|neon\s+tester|meter\s+se\s+fault|multimeter\s+se)\b", "electrical testing", 0.90),
    (r"\b(multimeter|tester|test\s+instrument|megger)\b", "use of test instruments", 0.85),
    # Distribution board
    (r"\b(distribution\s+board|DB\s+board|fuse\s+board|panel\s+board|MCB\s+board)\b", "distribution board installation", 0.88),
    (r"\b(MCB|ELCB|RCD|RCCB|circuit\s+breaker)\b", "circuit protection device installation", 0.82),
    # Earthing
    (r"\b(earthing|grounding|earth\s+wire|earth\s+lagana|earthing\s+karna)\b", "earthing installation", 0.88),
    # Safety
    (r"\b(safe\s+isolation|lockout|tagout|LOTO)\b", "safe isolation", 0.92),
    (r"\b(PPE|safety\s+equipment|protective\s+equipment|safety\s+helmet|gloves)\b", "safety equipment use", 0.84),
    # Planning
    (r"\b(electrical\s+drawing|wiring\s+diagram|circuit\s+diagram)\b", "reading electrical drawings", 0.87),
    (r"\b(permit|work\s+order|job\s+card)\b", "work permit and planning", 0.80),
]

# Compile once
_COMPILED_PATTERNS: list[tuple[re.Pattern, str, float]] = [
    (re.compile(pat, re.IGNORECASE | re.UNICODE), name, conf)
    for pat, name, conf in _ELECTRICIAN_PATTERNS
]


class DemoSkillExtractionProvider(SkillExtractionProvider):
    """
    Deterministic rule-based skill extraction for the electrician trade.

    Confidence values derive from pattern specificity (longer, more specific
    patterns get higher confidence). No random numbers are used.

    This provider works without any API keys or external models.
    """

    def extract_skills(
        self,
        text: str,
        language: str = "en",
        trade: str = "electrician",
    ) -> SKILLS_OUTPUT:
        if not text or not text.strip():
            return []

        seen_skills: dict[str, dict] = {}

        for pattern, skill_name, base_confidence in _COMPILED_PATTERNS:
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            # Use the first match's text as evidence_text
            evidence_text = matches[0].group(0).strip()
            normalized = normalise_with_glossary(skill_name, trade)

            # Only keep the highest-confidence pattern per normalized skill
            if normalized not in seen_skills or seen_skills[normalized]["confidence"] < base_confidence:
                seen_skills[normalized] = {
                    "skill_name": skill_name,
                    "normalized_name": normalized,
                    "evidence_text": evidence_text,
                    "confidence": base_confidence,
                }

        results = list(seen_skills.values())
        # Sort by confidence descending for stable ordering
        results.sort(key=lambda x: (-x["confidence"], x["skill_name"]))
        return results

    @property
    def provider_name(self) -> str:
        return "demo-rule-based-v1"


# ---------------------------------------------------------------------------
# LLM-based provider placeholder
# ---------------------------------------------------------------------------

class LLMSkillExtractionProvider(SkillExtractionProvider):
    """
    Placeholder for LLM-based skill extraction.
    Falls back to DemoSkillExtractionProvider when no API key is configured.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key
        self._model = model
        self._fallback = DemoSkillExtractionProvider()

    def extract_skills(
        self,
        text: str,
        language: str = "en",
        trade: str = "electrician",
    ) -> SKILLS_OUTPUT:
        if not self._api_key:
            # No key — use deterministic fallback
            return self._fallback.extract_skills(text, language, trade)
        # Future: call LLM API here
        # For now always fallback
        return self._fallback.extract_skills(text, language, trade)

    @property
    def provider_name(self) -> str:
        return f"llm-{self._model}" if self._api_key else "llm-fallback-to-demo"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_skill_extraction_provider(
    provider_name: str = "demo",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> SkillExtractionProvider:
    if provider_name == "llm":
        return LLMSkillExtractionProvider(api_key=api_key, model=model)
    return DemoSkillExtractionProvider()
