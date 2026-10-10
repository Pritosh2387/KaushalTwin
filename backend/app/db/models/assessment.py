"""
KaushalTwin Backend — ORM Models: Assessment, AssessmentTask

Assessment lifecycle:
  DRAFT → IN_PROGRESS → READY_FOR_REVIEW → REVIEWED → CLOSED

Task lifecycle:
  PENDING → IN_PROGRESS → COMPLETED → SKIPPED

AI-recommended tasks are stored with selection_source=AI_RECOMMENDED.
When an assessor accepts, modifies, or assigns a task, selection_source
is updated to ASSESSOR_ASSIGNED to preserve provenance.
"""

from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AssessmentLifecycle(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REVIEWED = "REVIEWED"
    CLOSED = "CLOSED"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class TaskSelectionSource(str, enum.Enum):
    AI_RECOMMENDED = "AI_RECOMMENDED"
    ASSESSOR_ASSIGNED = "ASSESSOR_ASSIGNED"
    MODIFIED_FROM_AI = "MODIFIED_FROM_AI"


class Assessment(Base, TimestampMixin):
    """
    An assessment session linking a worker to an assessor.
    Tracks the lifecycle from draft to closed.
    """

    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("worker_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    trade: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AssessmentLifecycle] = mapped_column(
        Enum(AssessmentLifecycle, name="assessmentlifecycle"),
        nullable=False,
        default=AssessmentLifecycle.DRAFT,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps for lifecycle events
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    worker: Mapped["WorkerProfile"] = relationship(  # noqa: F821
        "WorkerProfile", back_populates="assessments"
    )
    assessor: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="assessed_assessments",
        foreign_keys=[assessor_id],
    )
    tasks: Mapped[list["AssessmentTask"]] = relationship(
        "AssessmentTask", back_populates="assessment", lazy="selectin"
    )
    ai_runs: Mapped[list["AIAssessmentRun"]] = relationship(  # noqa: F821
        "AIAssessmentRun", back_populates="assessment", lazy="selectin"
    )
    decisions: Mapped[list["AssessorDecision"]] = relationship(  # noqa: F821
        "AssessorDecision", back_populates="assessment", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Assessment id={self.id} worker={self.worker_id} status={self.status}>"


class AssessmentTask(Base, TimestampMixin):
    """
    A single assessment task within an assessment.
    Stores both AI-recommended and assessor-assigned tasks distinctly.
    """

    __tablename__ = "assessment_tasks"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Task definition
    ml_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_nos_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Provenance — did AI select this or did the assessor?
    selection_source: Mapped[TaskSelectionSource] = mapped_column(
        Enum(TaskSelectionSource, name="taskselectionsource"),
        nullable=False,
        default=TaskSelectionSource.AI_RECOMMENDED,
    )
    ai_priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list stored as text

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"),
        nullable=False,
        default=TaskStatus.PENDING,
    )

    # Evaluation criteria (stored as JSON text)
    evaluation_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Result fields
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    assessor_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_references: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<AssessmentTask id={self.id} title={self.title!r} status={self.status}>"
