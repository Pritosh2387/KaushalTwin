"""
KaushalTwin Backend — ORM Model: WorkerProfile

Stores the occupational and experiential profile of an assessed worker.
A worker may or may not have a linked User account (assessors can register
workers on behalf of them).
"""

from __future__ import annotations

import uuid
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AssessmentStatus(str, enum.Enum):
    """High-level status for a worker's assessment journey."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CERTIFIED = "CERTIFIED"   # set manually by admin only


class WorkerProfile(Base, TimestampMixin):
    """
    Occupational and experiential profile of a worker.

    Separate from the User model so that assessors can create worker
    profiles for walk-in candidates who may not have platform accounts.
    """

    __tablename__ = "worker_profiles"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)

    # Optional link to a login account
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Occupational information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade: Mapped[str] = mapped_column(String(255), nullable=False)
    years_of_experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    experience_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    education_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Journey status
    assessment_status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, name="assessmentstatus"),
        nullable=False,
        default=AssessmentStatus.NOT_STARTED,
    )

    # Registered-by (assessor or admin who created this profile)
    registered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # ── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="worker_profile", foreign_keys=[user_id]
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # noqa: F821
        "Assessment", back_populates="worker", lazy="selectin"
    )
    evidence_records: Mapped[list["EvidenceRecord"]] = relationship(  # noqa: F821
        "EvidenceRecord", back_populates="worker", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<WorkerProfile id={self.id} name={self.full_name!r} trade={self.trade!r}>"
