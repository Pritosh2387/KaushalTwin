"""
KaushalTwin Backend — ORM Model: User

Roles:
  WORKER   — assessed individual
  ASSESSOR — certified assessor who reviews and decides
  ADMIN    — platform administrator
"""

from __future__ import annotations

import uuid
import enum

from sqlalchemy import Boolean, Enum, String, UniqueConstraint
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    WORKER = "WORKER"
    ASSESSOR = "ASSESSOR"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin):
    """
    Platform user account.

    Workers log in and view their own data.
    Assessors manage and evaluate assessments.
    Admins manage the platform.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[uuid.UUID] = mapped_column(
        TEXT,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.WORKER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ────────────────────────────────────────────────────────
    worker_profile: Mapped["WorkerProfile"] = relationship(  # noqa: F821
        "WorkerProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    assessed_assessments: Mapped[list["Assessment"]] = relationship(  # noqa: F821
        "Assessment",
        back_populates="assessor",
        foreign_keys="Assessment.assessor_id",
        lazy="selectin",
    )
    decisions: Mapped[list["AssessorDecision"]] = relationship(  # noqa: F821
        "AssessorDecision", back_populates="assessor", lazy="selectin"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(  # noqa: F821
        "AuditEvent", back_populates="actor_user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
