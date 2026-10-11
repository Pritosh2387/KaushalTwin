"""
KaushalTwin Backend — AuditEvent Model
"""

from __future__ import annotations

from app.db.enums import AuditEventType
from app.db.models.mongo_models import AuditEvent

__all__ = ["AuditEvent", "AuditEventType"]
