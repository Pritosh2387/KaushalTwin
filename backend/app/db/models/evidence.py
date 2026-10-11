"""
KaushalTwin Backend — EvidenceRecord Model
"""

from __future__ import annotations

from app.db.enums import EvidenceType, EvidenceSourceType, EvidenceVerificationStatus, VerificationStatus
from app.db.models.mongo_models import EvidenceRecord

__all__ = [
    "EvidenceRecord",
    "EvidenceType",
    "EvidenceSourceType",
    "EvidenceVerificationStatus",
    "VerificationStatus",
]
