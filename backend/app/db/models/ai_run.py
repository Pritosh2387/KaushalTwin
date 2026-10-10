"""
KaushalTwin Backend — ORM Model: AIAssessmentRun

Stores the full input snapshot and structured output of each ML pipeline
invocation. The ML service is stateless; this table is the persistence layer
for all ML analysis history.

IMPORTANT: AI runs are immutable once created. A new run is created for each
pipeline invocation. Existing runs are never overwritten.
"""

from __future__ import annotations

import uuid
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AIAssessmentRun(Base, TimestampMixin):
    """
    Persists one invocation of the ML pipeline for a worker assessment.

    Fields:
      - input_snapshot_json: safe serialization of inputs sent to ML service
      - ml_response_json:    full structured response from the ML service
      - recommendation:      top-level recommendation enum from ML (denormalized)
      - run_status:          lifecycle status of this run
      - error_detail:        message if the ML service returned an error
    """

    __tablename__ = "ai_assessment_runs"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("worker_profiles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    triggered_by_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # ML service version/metadata
    ml_service_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ml_pipeline_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Inputs (safe audit reference — no raw credentials or secrets)
    input_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full ML response (JSON)
    ml_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Commonly queried fields denormalized from ml_response_json
    recommendation: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Status
    run_status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="runstatus"),
        nullable=False,
        default=RunStatus.PENDING,
        index=True,
    )
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(  # noqa: F821
        "Assessment", back_populates="ai_runs"
    )

    def __repr__(self) -> str:
        return (
            f"<AIAssessmentRun id={self.id} assessment={self.assessment_id} "
            f"status={self.run_status} recommendation={self.recommendation}>"
        )
