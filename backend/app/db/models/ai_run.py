"""
KaushalTwin Backend — AIAssessmentRun Model
"""

from __future__ import annotations

from app.db.enums import RunStatus
from app.db.models.mongo_models import AIAssessmentRun

__all__ = ["AIAssessmentRun", "RunStatus"]
