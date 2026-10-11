"""
KaushalTwin Backend — User Model
"""

from __future__ import annotations

from app.db.enums import UserRole
from app.db.models.mongo_models import User

__all__ = ["User", "UserRole"]
