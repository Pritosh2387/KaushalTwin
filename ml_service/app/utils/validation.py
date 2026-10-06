"""
KaushalTwin ML Service — Input Validation Utilities
"""

from __future__ import annotations

from fastapi import HTTPException


def require_non_empty_text(text: str, field_name: str = "text") -> str:
    """Raise 422 if text is blank or whitespace-only."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "INVALID_INPUT",
                    "message": f"'{field_name}' cannot be empty.",
                }
            },
        )
    return text.strip()


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a float to [lo, hi]."""
    return max(lo, min(hi, value))
