"""
KaushalTwin ML Service — Trade Alias & Synonym Registry
Priority 5: Trade-Agnostic Skill Extraction

Provides configurable per-trade synonym/alias maps and shared cross-trade
keyword patterns. Used by skill extraction and NOS mapping to bridge
informal language, regional terms, and spelling variations to canonical
skill names.

NOTE: All synonyms and aliases here are general occupational vocabulary.
They do NOT represent official NCVET/NSDC terminology.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

# Mapping: canonical_skill_name -> list of aliases/synonyms (lowercase)
SynonymMap = Dict[str, List[str]]


# ---------------------------------------------------------------------------
# General / cross-trade patterns
# These cover skills expressed in natural language that apply across trades.
# ---------------------------------------------------------------------------

GENERAL_SYNONYMS: SynonymMap = {
    "safety equipment use": [
        "ppe", "personal protective equipment", "safety gear",
        "helmet", "hard hat", "gloves", "safety boots", "goggles",
        "safety glasses", "ear protection", "face shield",
        "safety harness", "hi-vis", "protective clothing",
        # Hindi/Hinglish
        "safety wala kapda", "helmet lagana", "dastane",
    ],
    "work planning": [
        "planning", "preparation", "work order", "job card",
        "work permit", "method statement", "risk assessment",
        "task planning", "work sequence",
    ],
    "safety compliance": [
        "safety rules", "safe working", "health and safety",
        "osha", "is code", "nbc", "regulations", "compliance",
        "hazard identification", "risk control",
    ],
    "fault diagnosis": [
        "troubleshooting", "fault finding", "finding faults",
        "diagnose", "diagnosis", "identify fault", "locate fault",
        "defect identification", "problem finding",
        # Hindi/Hinglish
        "garbari dhundna", "kharaabi nikalna",
    ],
    "inspection": [
        "visual inspection", "check", "checking", "testing",
        "quality check", "qc", "verify", "verification",
        "examine", "survey",
    ],
    "tool use": [
        "hand tools", "power tools", "equipment operation",
        "instrument use", "measurement",
    ],
    "maintenance": [
        "maintenance", "servicing", "upkeep", "preventive maintenance",
        "pm", "routine maintenance",
    ],
    "repair": [
        "repair", "fix", "rectify", "rework", "replace",
        "restoration", "corrective maintenance",
    ],
}


# ---------------------------------------------------------------------------
# Electrician-specific synonyms
# ---------------------------------------------------------------------------

ELECTRICIAN_SYNONYMS: SynonymMap = {
    "electrical wiring": [
        "wiring", "house wiring", "domestic wiring", "internal wiring",
        "cable laying", "wire", "cabling",
        # Hindi/Hinglish
        "ghar ki wiring", "bijli ki wiring", "wiring karna",
    ],
    "switch installation": [
        "switch", "switches", "switch fitting", "switch lagana",
        "switch board", "modular switch", "switch repair",
        # Hindi/Hinglish
        "switch lagana", "switch fit karna",
    ],
    "fan installation": [
        "fan", "fans", "ceiling fan", "fan fitting",
        "fan lagana", "fan wiring",
        # Hindi/Hinglish
        "pankha lagana", "ceiling fan lagana",
    ],
    "light fixture installation": [
        "light", "lights", "lighting", "light point", "light fitting",
        "bulb holder", "tube light", "led light", "light install",
    ],
    "socket outlet installation": [
        "socket", "sockets", "outlet", "plug point", "power point",
        "point lagana",
        # Hindi/Hinglish
        "socket lagana",
    ],
    "electrical fault diagnosis": [
        "fault finding", "fault diagnosis", "troubleshoot",
        "find fault", "fault dhundna",
        "bijli ki garbari", "line testing",
        # Instruments
        "multimeter use", "tester use", "line tester",
    ],
    "electrical testing": [
        "line tester", "voltage tester", "phase tester",
        "neon tester", "multimeter", "testing with meter",
        "meter se check karna",
    ],
    "use of test instruments": [
        "multimeter", "tester", "test instrument", "megger",
        "clamp meter", "instrument use",
    ],
    "distribution board installation": [
        "distribution board", "db board", "fuse board",
        "panel board", "mcb board", "switchboard installation",
        "db kaam", "panel kaam",
    ],
    "circuit protection device installation": [
        "mcb", "elcb", "rcd", "rccb", "circuit breaker",
        "fuse", "safety device",
    ],
    "earthing installation": [
        "earthing", "grounding", "earth wire", "earth connection",
        "earthing lagana", "earth karna",
    ],
    "safe isolation": [
        "safe isolation", "lockout", "tagout", "loto",
        "isolate circuit", "switch off supply",
    ],
    "reading electrical drawings": [
        "electrical drawing", "wiring diagram", "circuit diagram",
        "schematic", "layout drawing",
    ],
    "conduit installation": [
        "conduit", "conduit pipe", "pipe mein wire",
        "conduit wiring", "GI conduit",
    ],
}


# ---------------------------------------------------------------------------
# Plumber-specific synonyms
# ---------------------------------------------------------------------------

PLUMBER_SYNONYMS: SynonymMap = {
    "pipe installation": [
        "pipe", "pipes", "pipework", "piping", "plumbing",
        "pipe fitting", "pipe laying", "pipe jointing",
        "pipe lagana", "paani ki pipe",
        # Types
        "cpvc pipe", "pvc pipe", "gi pipe", "copper pipe", "upvc pipe",
        "ppr pipe",
    ],
    "water supply installation": [
        "water supply", "water line", "water pipe",
        "cold water", "hot water", "water connection",
        "paani ki line", "paani ka connection",
    ],
    "drainage installation": [
        "drainage", "drain pipe", "waste pipe", "soil pipe",
        "sewage", "sewer", "drainage system", "drain laying",
        "nali", "naali", "gutter",
    ],
    "sanitary fixture installation": [
        "toilet", "wc", "commode", "water closet",
        "cistern", "flush tank", "overhead tank",
        "wash basin", "basin", "sink", "bathroom fitting",
        "shower", "bath", "bathtub", "shower fitting",
        # Hindi/Hinglish
        "toilet lagana", "commode fit karna", "basin lagana",
        "shower lagana",
    ],
    "tap and valve fitting": [
        "tap", "taps", "faucet", "valve", "gate valve",
        "ball valve", "stop cock", "water tap",
        "nal", "nala", "nal lagana",
    ],
    "pipe jointing": [
        "joint", "jointing", "soldering", "compression fitting",
        "push fit", "cement joint", "welding pipe",
        "threaded joint", "flanged joint",
    ],
    "plumbing leak repair": [
        "leak", "leaking", "leakage", "water leak",
        "pipe leak", "repair leak", "fix leak",
        "seepage", "seep",
        # Hindi/Hinglish
        "choot raha hai", "tapka", "tapakna",
    ],
    "drain blockage clearance": [
        "blockage", "blocked", "clogged", "choke",
        "blocked drain", "drain cleaning", "clear blockage",
        "choked drain", "unblock",
    ],
    "water storage installation": [
        "water tank", "overhead tank", "sump", "storage tank",
        "tank installation", "water storage",
        "paani tank",
    ],
    "plumbing drawings": [
        "plumbing drawing", "isometric drawing", "layout",
        "plumbing plan", "schematic",
    ],
}


# ---------------------------------------------------------------------------
# Welder-specific synonyms
# ---------------------------------------------------------------------------

WELDER_SYNONYMS: SynonymMap = {
    "arc welding": [
        "mma welding", "smaw", "stick welding", "arc welding",
        "manual metal arc", "electrode welding",
        "welding rod", "welding karna", "jointing by welding",
    ],
    "mig welding": [
        "mig welding", "mag welding", "gmaw", "wire welding",
        "semi automatic welding", "mig",
    ],
    "tig welding": [
        "tig welding", "gtaw", "argon welding", "tungsten welding",
        "gas tungsten arc", "tig",
    ],
    "gas welding": [
        "gas welding", "oxyacetylene", "oxy-acetylene", "torch welding",
        "flame welding",
    ],
    "welding setup": [
        "welding machine setup", "set machine", "electrode selection",
        "current setting", "amperage", "wire setup", "gas setup",
        "shielding gas", "polarity",
    ],
    "weld inspection": [
        "weld inspection", "visual inspection of weld", "check weld",
        "weld quality", "porosity", "undercut", "weld defect",
        "ndt", "non-destructive testing",
    ],
    "cutting operations": [
        "cutting", "gas cutting", "flame cutting", "plasma cutting",
        "grinding", "angle grinder", "disc cutting",
    ],
    "joint preparation": [
        "joint preparation", "bevel", "bevelling", "chamfer",
        "edge preparation", "groove", "v-groove", "butt preparation",
    ],
    "welding safety": [
        "welding helmet", "welding mask", "welding gloves",
        "welding fumes", "ventilation", "eye protection",
        "uv radiation", "spatter protection",
    ],
    "reading welding drawings": [
        "welding drawing", "weld symbol", "weld notation",
        "drawing interpretation", "blueprint",
    ],
}


# ---------------------------------------------------------------------------
# Mason-specific synonyms
# ---------------------------------------------------------------------------

MASON_SYNONYMS: SynonymMap = {
    "bricklaying": [
        "brick", "bricks", "bricklaying", "brick laying",
        "brick work", "brickwork", "masonry", "laying bricks",
        "eet", "eet lagana", "eetein lagana",
    ],
    "block work": [
        "block", "blocks", "blockwork", "hollow block", "cement block",
        "block laying", "aac block",
    ],
    "mortar mixing": [
        "mortar", "cement mortar", "mixing", "mix cement",
        "sand cement mix", "concrete mix", "cement mixing",
        "cement", "sand", "ratio",
        # Hindi/Hinglish
        "mortar banana", "cement banana", "cement mix karna",
    ],
    "plastering": [
        "plaster", "plastering", "render", "rendering",
        "wall finish", "cement plaster", "wall plastering",
        "putty", "skim coat", "internal plaster", "external plaster",
        # Hindi/Hinglish
        "plaster karna", "lipai karna", "lipai",
    ],
    "setting out": [
        "setting out", "layout", "marking", "datum",
        "building lines", "grid line", "level marking",
        "plumb line", "string line",
    ],
    "scaffolding": [
        "scaffold", "scaffolding", "bamboo scaffolding",
        "working platform", "staging", "ladder",
    ],
    "concrete work": [
        "concrete", "concrete mix", "rcc", "reinforced concrete",
        "shuttering", "formwork", "casting", "concrete pour",
    ],
    "tile laying": [
        "tile", "tiles", "tiling", "tile laying", "floor tile",
        "wall tile", "ceramic tile", "vitrified tile",
        "tiles lagana",
    ],
}


# ---------------------------------------------------------------------------
# Registry: trade name -> synonym map
# ---------------------------------------------------------------------------

TRADE_SYNONYM_REGISTRY: Dict[str, SynonymMap] = {
    "electrician": ELECTRICIAN_SYNONYMS,
    "plumber": PLUMBER_SYNONYMS,
    "welder": WELDER_SYNONYMS,
    "mason": MASON_SYNONYMS,
    "general": {},
}


# ---------------------------------------------------------------------------
# Reverse lookup: alias -> canonical skill name for a given trade
# ---------------------------------------------------------------------------

def _build_reverse_map(synonym_map: SynonymMap) -> Dict[str, str]:
    """Build a reverse lookup from alias (lowercase) -> canonical skill name."""
    reverse: Dict[str, str] = {}
    for canonical, aliases in synonym_map.items():
        reverse[canonical.lower()] = canonical
        for alias in aliases:
            reverse[alias.lower()] = canonical
    return reverse


def get_reverse_map(trade: str) -> Dict[str, str]:
    """Return reverse lookup map for a trade, merging general and trade-specific."""
    general_reverse = _build_reverse_map(GENERAL_SYNONYMS)
    trade_reverse = _build_reverse_map(TRADE_SYNONYM_REGISTRY.get(trade.lower(), {}))
    # Trade-specific entries take precedence over general ones
    return {**general_reverse, **trade_reverse}


def get_all_aliases(trade: str) -> Dict[str, str]:
    """Return all alias->canonical mappings for the given trade including general."""
    return get_reverse_map(trade)


def normalize_skill_via_synonyms(phrase: str, trade: str = "general") -> str:
    """
    Normalize a skill phrase using trade-specific and general synonyms.
    Returns the canonical skill name if found, otherwise the lowercased phrase.
    """
    phrase_lower = phrase.strip().lower()
    reverse_map = get_reverse_map(trade)
    # Exact match
    if phrase_lower in reverse_map:
        return reverse_map[phrase_lower]
    # Partial match: check if phrase contains any alias
    for alias, canonical in sorted(reverse_map.items(), key=lambda x: -len(x[0])):
        if alias in phrase_lower:
            return canonical
    return phrase_lower


# ---------------------------------------------------------------------------
# Trade detection from text
# ---------------------------------------------------------------------------

# Trade-indicator keywords: trade -> high-value keywords that strongly suggest that trade
TRADE_INDICATORS: Dict[str, List[str]] = {
    "electrician": [
        "wiring", "wire", "cable", "conduit", "switch", "switches",
        "fan", "fans", "ceiling fan", "socket", "outlet", "plug",
        "mcb", "elcb", "rcd", "circuit", "distribution board", "fuse",
        "earthing", "grounding", "voltage", "current", "electrical",
        "multimeter", "tester", "line tester", "phase tester", "megger",
        "loto", "lockout", "bijli", "pankha", "switch lagana", "ghar ki wiring",
    ],
    "plumber": [
        "plumbing", "plumber", "pipe", "pipes", "pipework", "piping",
        "cpvc", "pvc", "upvc", "gi pipe", "copper pipe", "water supply",
        "tap", "taps", "faucet", "valve", "stop cock", "drainage",
        "drain", "waste pipe", "soil pipe", "sewer", "sewage", "trap",
        "p-trap", "s-trap", "toilet", "wc", "commode", "cistern",
        "flush", "wash basin", "basin", "sink", "shower", "bath",
        "geyser", "leak", "leaking", "leakage", "seepage", "blockage",
        "water tank", "overhead tank", "paani", "nal", "nali", "naali",
    ],
    "welder": [
        "welding", "welder", "weld", "welds", "mma", "smaw",
        "stick weld", "arc weld", "mig", "mag", "gmaw", "tig",
        "gtaw", "gas weld", "oxy-acetylene", "torch", "electrode",
        "filler wire", "shielding gas", "argon", "co2", "bevel",
        "bevelling", "chamfer", "v-groove", "butt joint", "fillet weld",
        "bead", "porosity", "undercut", "slag", "spatter", "welding helmet",
        "welding mask", "welding rod",
    ],
    "mason": [
        "masonry", "mason", "brick", "bricks", "bricklaying", "brickwork",
        "block", "blocks", "blockwork", "mortar", "cement", "sand",
        "plaster", "plastering", "render", "rendering", "wall",
        "trowel", "plumb line", "building line", "setting out",
        "scaffold", "scaffolding", "concrete", "rcc", "shuttering",
        "tile", "tiles", "tiling", "eet", "eetein", "lipai",
    ],
}


def detect_trade_from_text(text: str) -> Tuple[str, float]:
    """
    Heuristically detect the most likely trade from text using high-value indicator keywords.

    Returns (trade_name, confidence) where:
      - trade_name is one of 'electrician', 'plumber', 'welder', 'mason', 'ambiguous', or 'general'
      - confidence is a float in [0.0, 1.0]

    Uses word boundary matching to avoid accidental substrings.
    When multiple trades have comparable domain signals, classifies as 'ambiguous'.
    """
    import re
    text_lower = text.lower()
    scores: Dict[str, int] = {}

    for trade, indicators in TRADE_INDICATORS.items():
        score = 0
        for kw in indicators:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                score += 1
        if score > 0:
            scores[trade] = score

    if not scores:
        return "general", 0.0

    sorted_trades = sorted(scores.items(), key=lambda x: -x[1])
    best_trade, best_score = sorted_trades[0]

    # Only one trade detected
    if len(sorted_trades) == 1:
        conf = round(min(0.70 + best_score * 0.10, 0.98), 2)
        return best_trade, conf

    # Multiple trades detected: compare top 2
    second_trade, second_score = sorted_trades[1]

    # If the second trade also has strong signals or is close to best, it's ambiguous
    if second_score >= 2 or (best_score - second_score) <= 1:
        if (best_score - second_score) >= 3 and best_score >= second_score * 2:
            conf = round(min(0.60 + (best_score - second_score) * 0.10, 0.90), 2)
            return best_trade, conf
        else:
            return "ambiguous", 0.50
    else:
        conf = round(min(0.65 + (best_score - second_score) * 0.10, 0.92), 2)
        return best_trade, conf

