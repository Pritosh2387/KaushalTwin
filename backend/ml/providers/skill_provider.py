"""
KaushalTwin ML Service — Skill Extraction Provider Interface & Implementations
Module 2: Skill Intelligence & NOS Mapping

Priority 5: Extended to support trade-agnostic extraction across electrician,
plumber, welder, mason, and general trade descriptions using configurable
synonym/alias patterns and natural-language pattern matching.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ml.utils.normalisation import normalise_text, tokenise, extract_keywords
from ml.trade_registry import (
    ELECTRICIAN_SYNONYMS,
    PLUMBER_SYNONYMS,
    WELDER_SYNONYMS,
    MASON_SYNONYMS,
    GENERAL_SYNONYMS,
    detect_trade_from_text,
    normalize_skill_via_synonyms,
)

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
        trade: str = "general",
    ) -> SKILLS_OUTPUT:
        """
        Extract structured skills from the given text.

        Returns a list of skill dicts:
            skill_name       : str
            normalized_name  : str
            evidence_text    : str
            confidence       : float  — deterministic in demo mode
            trade_context    : str    — detected or specified trade
            text_span        : str    — matched text span
            extraction_method: str    — e.g. "pattern_match", "synonym_expand"
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


# ---------------------------------------------------------------------------
# Glossary loader (legacy — kept for backward compatibility)
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
    Attempt to normalise a raw phrase via the trade glossary,
    falling back to trade_registry synonyms, then returning lowercase phrase.
    """
    glossary = _load_glossary()
    phrase_lower = phrase.strip().lower()
    for entry in glossary.get("terms", []):
        candidates = [entry["local_term"].lower()] + [
            a.lower() for a in entry.get("aliases", [])
        ]
        if phrase_lower in candidates:
            return entry["normalized_term"]
    return normalize_skill_via_synonyms(phrase_lower, trade)


# ---------------------------------------------------------------------------
# Trade-specific pattern definitions
#
# Each pattern: (regex_pattern, skill_name, base_confidence)
#
# Confidence reflects pattern specificity:
#   - Compound/precise patterns (longer regex, more context) → higher confidence
#   - Standalone generic keyword → lower confidence
#
# Patterns are compiled once per trade, not on every call.
# ---------------------------------------------------------------------------

# ── Electrician patterns ─────────────────────────────────────────────────────
_ELECTRICIAN_PATTERNS: list[tuple[str, str, float]] = [
    # Wiring
    (r"\b(house\s+wiring|domestic\s+wiring|ghar\s+ki\s+wiring|internal\s+wiring)\b",
     "house wiring", 0.93),
    (r"\b(wiring|wire)\b", "electrical wiring", 0.82),
    (r"\b(conduit|pipe\s+mein\s+wire)\b", "conduit installation", 0.80),
    # Switches
    (r"\b(switch\s+install\w*|install\w*\s+switch\w*|switch\s+lagana|switch\s+fit)\b",
     "switch installation", 0.92),
    (r"\bswitch(es)?\b", "switch installation", 0.78),
    # Fans
    (r"\b(fan\s+install\w*|install\w*\s+fan\w*|ceiling\s+fan\w*|pankha\s+lagana|fan\s+fit)\b",
     "fan installation", 0.91),
    (r"\bfan(s)?\b", "fan installation", 0.76),
    # Fixtures
    (r"\b(light\s+point|light\s+install\w*|light\s+fixture\w*)\b",
     "light fixture installation", 0.85),
    (r"\b(socket\w*|outlet\w*|plug\s+point|power\s+point|point\s+lagana)\b",
     "socket outlet installation", 0.84),
    # Fault finding
    (r"\b(fault\s+find\w*|fault\s+diagnos\w*|fault\s+dhundh\w*|troubleshoot\w*"
     r"|fault\s+nikalna|bijli\s+ki\s+garbari)\b",
     "electrical fault diagnosis", 0.92),
    (r"\bfind\w*\s+fault\w*\b", "electrical fault diagnosis", 0.88),
    (r"\bfault(s)?\b", "electrical fault diagnosis", 0.72),
    # Testing
    (r"\b(line\s+tester|voltage\s+tester|phase\s+tester|neon\s+tester"
     r"|meter\s+se\s+fault|multimeter\s+se)\b",
     "electrical testing", 0.90),
    (r"\b(multimeter|tester\w*|test\s+instrument|megger)\b",
     "use of test instruments", 0.85),
    # Distribution board
    (r"\b(distribution\s+board|DB\s+board|fuse\s+board|panel\s+board|MCB\s+board)\b",
     "distribution board installation", 0.88),
    (r"\b(MCB|ELCB|RCD|RCCB|circuit\s+breaker)\b",
     "circuit protection device installation", 0.82),
    # Earthing
    (r"\b(earthing|grounding|earth\s+wire|earth\s+lagana|earthing\s+karna)\b",
     "earthing installation", 0.88),
    # Safety
    (r"\b(safe\s+isolation|lockout|tagout|LOTO)\b", "safe isolation", 0.92),
    (r"\b(PPE|safety\s+equipment|protective\s+equipment|safety\s+helmet|gloves)\b",
     "safety equipment use", 0.84),
    # Planning
    (r"\b(electrical\s+drawing|wiring\s+diagram|circuit\s+diagram)\b",
     "reading electrical drawings", 0.87),
    (r"\b(permit|work\s+order|job\s+card)\b", "work permit and planning", 0.80),
]

# ── Plumber patterns ─────────────────────────────────────────────────────────
_PLUMBER_PATTERNS: list[tuple[str, str, float]] = [
    # Pipe installation
    (r"\b(cpvc\s+pipe|pvc\s+pipe|gi\s+pipe|copper\s+pipe|ppr\s+pipe|upvc\s+pipe)\b",
     "pipe installation", 0.92),
    (r"\b(pipe\s+install\w*|install\w*\s+pipe\w*|pipe\s+fitting|pipe\s+lagana|pipework)\b",
     "pipe installation", 0.90),
    (r"\b(pipe|piping)\b", "pipe installation", 0.70),
    # Water supply
    (r"\b(water\s+supply|water\s+line|paani\s+ki\s+line|hot\s+water|cold\s+water)\b",
     "water supply installation", 0.90),
    # Drainage
    (r"\b(drainage|drain\s+pipe|waste\s+pipe|soil\s+pipe|sewage|sewer|naali|nali)\b",
     "drainage installation", 0.88),
    (r"\b(p.trap|s.trap|floor\s+trap|gully\s+trap|vent\s+pipe)\b",
     "drainage installation", 0.90),
    # Sanitary fixtures
    (r"\b(toilet|wc|commode|water\s+closet|cistern|flush)\b",
     "sanitary fixture installation", 0.90),
    (r"\b(wash\s+basin|basin|sink|bathroom\s+fitting|shower|bathtub)\b",
     "sanitary fixture installation", 0.88),
    (r"\b(toilet\s+lagana|commode\s+fit|basin\s+lagana|shower\s+lagana)\b",
     "sanitary fixture installation", 0.92),
    # Taps & valves
    (r"\b(tap|taps|faucet|valve|gate\s+valve|ball\s+valve|stop\s+cock|nal)\b",
     "tap and valve fitting", 0.85),
    # Pipe jointing
    (r"\b(soldering|compression\s+fitting|push\s+fit|threaded\s+joint|cement\s+joint)\b",
     "pipe jointing", 0.88),
    # Leak repair
    (r"\b(leak|leaking|leakage|water\s+leak|seepage|tapakna|choot)\b",
     "plumbing leak repair", 0.85),
    # Blockage
    (r"\b(blockage|blocked|clogged|choke|choked\s+drain|drain\s+cleaning)\b",
     "drain blockage clearance", 0.87),
    # Water storage
    (r"\b(water\s+tank|overhead\s+tank|sump|storage\s+tank|tank\s+install\w*)\b",
     "water storage installation", 0.88),
    # Safety
    (r"\b(PPE|safety\s+equipment|safety\s+boots|gloves|protective\s+clothing)\b",
     "safety equipment use", 0.82),
]

# ── Welder patterns ──────────────────────────────────────────────────────────
_WELDER_PATTERNS: list[tuple[str, str, float]] = [
    # MMA/SMAW
    (r"\b(MMA|SMAW|stick\s+weld\w*|manual\s+metal\s+arc|arc\s+weld\w*)\b",
     "arc welding", 0.93),
    (r"\b(electrode\s+weld\w*|rod\s+weld\w*|welding\s+rod|welding\s+karna)\b",
     "arc welding", 0.88),
    # MIG/MAG
    (r"\b(MIG\s+weld\w*|MAG\s+weld\w*|GMAW|wire\s+feed\w*|semi\s+automatic\s+weld\w*)\b",
     "mig welding", 0.93),
    # TIG
    (r"\b(TIG\s+weld\w*|GTAW|argon\s+weld\w*|tungsten\s+weld\w*)\b",
     "tig welding", 0.93),
    # Gas welding
    (r"\b(gas\s+weld\w*|oxy.acetylene|torch\s+weld\w*|flame\s+weld\w*)\b",
     "gas welding", 0.90),
    # Generic welding
    (r"\bweld\w*\b", "arc welding", 0.72),
    # Setup
    (r"\b(current\s+setting|amperage|polarity|electrode\s+select\w*|wire\s+setup)\b",
     "welding setup", 0.87),
    (r"\b(shielding\s+gas|argon|CO2|gas\s+flow)\b", "welding setup", 0.85),
    # Weld inspection
    (r"\b(weld\s+inspect\w*|weld\s+quality|porosity|undercut|weld\s+defect)\b",
     "weld inspection", 0.92),
    (r"\b(NDT|non.destructive\s+test\w*|visual\s+inspect\w*\s+weld)\b",
     "weld inspection", 0.90),
    # Cutting
    (r"\b(gas\s+cutting|flame\s+cutting|plasma\s+cutting|oxy.fuel\s+cutting)\b",
     "cutting operations", 0.90),
    (r"\b(angle\s+grinder|grinding|disc\s+cutting)\b", "cutting operations", 0.82),
    # Joint prep
    (r"\b(bevel|bevelling|chamfer|edge\s+preparation|v.groove|joint\s+prep\w*)\b",
     "joint preparation", 0.88),
    # Safety
    (r"\b(welding\s+helmet|welding\s+mask|welding\s+gloves|welding\s+fume)\b",
     "welding safety", 0.90),
    (r"\b(UV\s+radiation|spatter\s+protect\w*|fume\s+extraction)\b",
     "welding safety", 0.87),
    # Drawings
    (r"\b(welding\s+drawing|weld\s+symbol|weld\s+notation)\b",
     "reading welding drawings", 0.88),
    # Generic safety
    (r"\b(PPE|safety\s+equipment|protective\s+clothing|gloves)\b",
     "safety equipment use", 0.82),
]

# ── Mason patterns ────────────────────────────────────────────────────────────
_MASON_PATTERNS: list[tuple[str, str, float]] = [
    # Bricklaying
    (r"\b(bricklaying|brick\s+laying|brick\s+work|brickwork|laying\s+brick\w*)\b",
     "bricklaying", 0.93),
    (r"\b(brick|bricks|eet|eetein)\b", "bricklaying", 0.78),
    # Block work
    (r"\b(blockwork|block\s+work|hollow\s+block|cement\s+block|aac\s+block)\b",
     "block work", 0.90),
    (r"\bblock(s)?\b", "block work", 0.74),
    # Mortar
    (r"\b(mortar\s+mix\w*|cement\s+mortar|sand\s+cement|mortar\s+bana\w*)\b",
     "mortar mixing", 0.90),
    (r"\b(mortar|cement\s+mix)\b", "mortar mixing", 0.78),
    # Plastering
    (r"\b(plaster\w*|render\w*|lipai|cement\s+plaster|wall\s+finish)\b",
     "plastering", 0.88),
    (r"\b(scratch\s+coat|float\s+coat|skim\s+coat|finish\s+plaster)\b",
     "plastering", 0.90),
    # Setting out
    (r"\b(setting\s+out|building\s+line|plumb\s+line|string\s+line|datum\s+level)\b",
     "setting out", 0.90),
    # Scaffolding
    (r"\b(scaffold\w*|bamboo\s+scaffold|working\s+platform|staging)\b",
     "scaffolding", 0.88),
    # Concrete
    (r"\b(rcc|reinforced\s+concrete|shuttering|formwork|concrete\s+pour|concrete\s+mix)\b",
     "concrete work", 0.90),
    (r"\bconcrete\b", "concrete work", 0.76),
    # Tiles
    (r"\b(tile\s+laying|tiling|floor\s+tile\w*|wall\s+tile\w*|tiles\s+lagana)\b",
     "tile laying", 0.90),
    (r"\btile(s)?\b", "tile laying", 0.74),
    # Safety
    (r"\b(hard\s+hat|PPE|safety\s+boots|safety\s+equipment|gloves)\b",
     "safety equipment use", 0.82),
]

# ── General / cross-trade patterns ────────────────────────────────────────────
_GENERAL_PATTERNS: list[tuple[str, str, float]] = [
    (r"\b(PPE|safety\s+equipment|protective\s+equipment|hard\s+hat|gloves|safety\s+boots|safety\s+helmet)\b",
     "safety equipment use", 0.80),
    (r"\b(troubleshoot\w*|fault\s+find\w*|diagnos\w*|identify\s+fault\w*)\b",
     "fault diagnosis", 0.82),
    (r"\b(visual\s+inspect\w*|quality\s+check|qc|verify|inspection)\b",
     "inspection", 0.80),
    (r"\b(repair|fix\w*|rectif\w*|rework)\b", "repair", 0.75),
    (r"\b(maintenance|servicing|preventive\s+maintenance|routine\s+maintenance)\b",
     "maintenance", 0.80),
    (r"\b(work\s+order|job\s+card|work\s+permit|method\s+statement)\b",
     "work planning", 0.78),
]

# Trade -> compiled patterns
_TRADE_PATTERNS: dict[str, list[tuple[str, str, float]]] = {
    "electrician": _ELECTRICIAN_PATTERNS,
    "plumber": _PLUMBER_PATTERNS,
    "welder": _WELDER_PATTERNS,
    "mason": _MASON_PATTERNS,
    "general": _GENERAL_PATTERNS,
}

# Compile all patterns once
_COMPILED_TRADE_PATTERNS: dict[str, list[tuple[re.Pattern, str, float]]] = {
    trade: [
        (re.compile(pat, re.IGNORECASE | re.UNICODE), name, conf)
        for pat, name, conf in patterns
    ]
    for trade, patterns in _TRADE_PATTERNS.items()
}


def _run_patterns(
    text: str,
    trade: str,
    include_general: bool = True,
) -> list[tuple[str, str, float, str]]:
    """
    Run compiled patterns for the given trade (and optionally general patterns).

    Returns list of (skill_name, text_span, confidence, extraction_method).
    """
    compiled = list(_COMPILED_TRADE_PATTERNS.get(trade, []))
    if include_general and trade != "general":
        compiled = compiled + _COMPILED_TRADE_PATTERNS["general"]

    seen_skills: dict[str, tuple[str, str, float, str]] = {}

    for pattern, skill_name, base_confidence in compiled:
        matches = list(pattern.finditer(text))
        if not matches:
            continue

        text_span = matches[0].group(0).strip()
        normalized = normalise_with_glossary(skill_name, trade)

        # Keep the highest-confidence pattern per normalized skill
        if normalized not in seen_skills or seen_skills[normalized][2] < base_confidence:
            seen_skills[normalized] = (skill_name, text_span, base_confidence, "pattern_match")

    return list(seen_skills.values())


def _run_synonym_expand(
    text: str,
    trade: str,
) -> list[tuple[str, str, float, str]]:
    """
    Expand trade synonyms to identify additional skills not caught by regex patterns.

    Returns list of (canonical_skill_name, text_span, confidence, extraction_method).
    Does NOT duplicate skills already found by pattern matching.
    """
    from ml.trade_registry import get_all_aliases
    aliases = get_all_aliases(trade)
    text_lower = text.lower()

    found: dict[str, tuple[str, str, float, str]] = {}

    # Sort aliases by length descending so longer matches take priority
    for alias, canonical in sorted(aliases.items(), key=lambda x: -len(x[0])):
        if len(alias) < 3:
            continue
        if alias in text_lower:
            # Use whole-word-ish check for short aliases
            if len(alias) < 6:
                # Require word boundary for short terms
                pat = re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE)
                if not pat.search(text):
                    continue
            if canonical not in found:
                # Confidence scales with alias length: longer alias = more specific
                confidence = min(0.65 + len(alias) * 0.01, 0.85)
                found[canonical] = (canonical, alias, confidence, "synonym_expand")

    return list(found.values())


# ---------------------------------------------------------------------------
# Demo Skill Extraction Provider — Trade-Agnostic
# ---------------------------------------------------------------------------

class DemoSkillExtractionProvider(SkillExtractionProvider):
    """
    Deterministic rule-based skill extraction supporting multiple trades.

    Supports: electrician, plumber, welder, mason, general.
    When trade='general' (or unrecognized), auto-detects trade from text content
    and runs patterns for the detected trade plus general patterns.

    Confidence values derive from pattern specificity. No random numbers are used.
    Works without any API keys or external models.

    Priority 5: Extended with multi-trade support, synonym expansion,
    trade context annotation, text span reporting, and extraction method tracking.
    """

    def extract_skills(
        self,
        text: str,
        language: str = "en",
        trade: str = "general",
    ) -> SKILLS_OUTPUT:
        if not text or not text.strip():
            return []

        # Determine which trades to inspect
        effective_trade = trade.lower() if trade and trade.lower() in _TRADE_PATTERNS else "general"

        trades_to_run: list[str] = []
        trade_context_label: str = effective_trade

        if effective_trade != "general":
            trades_to_run = [effective_trade]
            trade_context_label = effective_trade
        else:
            detected_trade, confidence = detect_trade_from_text(text)
            if detected_trade in _TRADE_PATTERNS and detected_trade != "general":
                trades_to_run = [detected_trade]
                trade_context_label = detected_trade
            elif detected_trade == "ambiguous":
                trades_to_run = ["electrician", "plumber", "welder", "mason"]
                trade_context_label = "multi-trade"
            else:
                # No specific trade detected from keywords: scan all trades so no practical skill is missed
                trades_to_run = ["electrician", "plumber", "welder", "mason"]
                trade_context_label = "general"

        # Run patterns across selected trades
        all_pattern_results = []
        for t in trades_to_run:
            pattern_res = _run_patterns(text, t, include_general=False)
            for skill_name, text_span, conf, method in pattern_res:
                all_pattern_results.append((skill_name, text_span, conf, method, t))

        # Always run general patterns as well
        general_res = _run_patterns(text, "general", include_general=False)
        for skill_name, text_span, conf, method in general_res:
            all_pattern_results.append((skill_name, text_span, conf, method, "general"))

        # Synonym expansion for trades_to_run + general
        found_skills = {r[0] for r in all_pattern_results}
        all_synonym_results = []
        for t in trades_to_run + ["general"]:
            syn_res = _run_synonym_expand(text, t)
            for skill_name, text_span, conf, method in syn_res:
                if skill_name not in found_skills:
                    all_synonym_results.append((skill_name, text_span, conf, method, t))

        # Deduplicate and keep highest-confidence per normalized name
        seen_skills: dict[str, dict] = {}
        for skill_name, text_span, conf, method, sk_trade in (all_pattern_results + all_synonym_results):
            normalized = normalise_with_glossary(skill_name, sk_trade)
            if normalized not in seen_skills or seen_skills[normalized]["confidence"] < conf:
                seen_skills[normalized] = {
                    "skill_name": skill_name,
                    "normalized_name": normalized,
                    "evidence_text": text_span,
                    "confidence": conf,
                    "trade_context": sk_trade if trade_context_label in ("multi-trade", "general") else trade_context_label,
                    "text_span": text_span,
                    "extraction_method": method,
                }

        results = list(seen_skills.values())
        # Sort by confidence descending, then by skill_name for stable ordering
        results.sort(key=lambda x: (-x["confidence"], x["skill_name"]))
        return results

    @property
    def provider_name(self) -> str:
        return "demo-rule-based-v2-multi-trade"


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
        trade: str = "general",
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
