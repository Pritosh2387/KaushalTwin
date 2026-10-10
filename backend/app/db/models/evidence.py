"""
KaushalTwin Backend — ORM Model: EvidenceRecord

Stores metadata and file references for evidence submitted by workers.
Large binary files are stored on disk (or object storage); only the path
and a SHA-256 content hash are persisted here.

Verification is a separate explicit action — uploaded files are NOT
automatically treated as verified.
"""

from __future__ import annotations

import uuid
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EvidenceType(str, enum.Enum):
    SELF_DECLARATION = "SELF_DECLARATION"
    CERTIFICATE = "CERTIFICATE"
    PHOTOGRAPH = "PHOTOGRAPH"
    VIDEO = "VIDEO"
    EMPLOYER_LETTER = "EMPLOYER_LETTER"
    PEER_REFERENCE = "PEER_REFERENCE"
    OBSERVATION_REPORT = "OBSERVATION_REPORT"
    PRACTICAL_TEST = "PRACTICAL_TEST"
    OTHER = "OTHER"


class EvidenceSourceType(str, enum.Enum):
    SELF = "SELF"
    EMPLOYER = "EMPLOYER"
    ASSESSOR = "ASSESSOR"
    THIRD_PARTY = "THIRD_PARTY"


class EvidenceVerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class EvidenceRecord(Base, TimestampMixin):
    """
    Metadata record for a piece of evidence.
    Binary data is stored on disk; this table holds the reference and hash.
    """

    __tablename__ = "evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Classification
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidencetype"), nullable=False
    )
    source_type: Mapped[EvidenceSourceType] = mapped_column(
        Enum(EvidenceSourceType, name="evidencesourcetype"), nullable=False
    )

    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    nos_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # File reference (server-side safe name)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)  # original filename
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA-256

    # Verification
    verification_status: Mapped[EvidenceVerificationStatus] = mapped_column(
        Enum(EvidenceVerificationStatus, name="evidenceverificationstatus"),
        nullable=False,
        default=EvidenceVerificationStatus.UNVERIFIED,
        index=True,
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extra metadata (JSON text for flexibility)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    worker: Mapped["WorkerProfile"] = relationship(  # noqa: F821
        "WorkerProfile", back_populates="evidence_records"
    )

    def __repr__(self) -> str:
        return (
            f"<EvidenceRecord id={self.id} type={self.evidence_type} "
            f"status={self.verification_status}>"
        )
