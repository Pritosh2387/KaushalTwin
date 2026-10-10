"""
KaushalTwin Backend — ORM Model: AssessorDecision

The final human decision on an assessment is an INDEPENDENT record.
It is never automatically overwritten by AI output.

Supported actions:
  ACCEPT_RECOMMENDATION     — assessor agrees with AI
  REJECT_RECOMMENDATION     — assessor disagrees
  REQUEST_MORE_EVIDENCE     — assessor needs more information
  MODIFY_RECOMMENDATION     — assessor amends the recommendation
"""

from __future__ import annotations

import uuid
import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DecisionAction(str, enum.Enum):
    ACCEPT_RECOMMENDATION = "ACCEPT_RECOMMENDATION"
    REJECT_RECOMMENDATION = "REJECT_RECOMMENDATION"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    MODIFY_RECOMMENDATION = "MODIFY_RECOMMENDATION"


class AssessorDecision(Base, TimestampMixin):
    """
    Final assessor action on an assessment.

    The original AI recommendation (in AIAssessmentRun) is never modified.
    This record stores the independent human decision alongside a reference
    to the AI run it responds to.
    """

    __tablename__ = "assessor_decisions"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("ai_assessment_runs.id", ondelete="SET NULL"), nullable=True
    )
    assessor_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    action: Mapped[DecisionAction] = mapped_column(
        Enum(DecisionAction, name="decisionaction"), nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # If assessor modifies the recommendation, what is the modified recommendation?
    modified_recommendation: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    assessment: Mapped["Assessment"] = relationship(  # noqa: F821
        "Assessment", back_populates="decisions"
    )
    assessor: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="decisions"
    )

    def __repr__(self) -> str:
        return (
            f"<AssessorDecision id={self.id} assessment={self.assessment_id} "
            f"action={self.action}>"
        )
