"""
KaushalTwin ML Service — Pydantic Schemas: Preprocessing (Module 1)
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PreprocessRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw transcript or text to preprocess")
    language: Optional[str] = Field(None, description="BCP-47 language code (e.g. 'hi', 'en'). Auto-detected if omitted.")
    lowercase: bool = Field(False, description="Lowercase the normalised text")

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text cannot be blank or whitespace only")
        return v


class PreprocessResponse(BaseModel):
    original_text: str = Field(..., description="Original input text")
    normalized_text: str = Field(..., description="Text after Unicode, whitespace and punctuation normalization")
    language: str = Field(..., description="Detected or provided language code (hi, en, mixed)")
    tokens: List[str] = Field(..., description="List of normalized tokens")
    sentences: List[str] = Field(..., description="List of normalized sentences")
    token_count: int = Field(..., ge=0, description="Number of tokens")
    sentence_count: int = Field(..., ge=0, description="Number of sentences")