"""
KaushalTwin ML Service — Pydantic Schemas: Preprocessing (Module 1)
"""

from __future__ import annotations
from typing import Optional
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
    original_text: str
    normalized_text: str
    language: str
    tokens: list[str]
    sentences: list[str]
    token_count: int
    sentence_count: int
