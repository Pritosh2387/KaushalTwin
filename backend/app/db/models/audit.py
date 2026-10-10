"""
KaushalTwin Backend — ORM Model: AuditEvent

Append-only log of significant system events.
Each event includes a SHA-256 integrity hash of the event data.

CRITICAL: No public API may DELETE or UPDATE audit events.
Ordinary users cannot read other users' audit events through public APIs.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AuditEvent(Base, TimestampMixin):
    """
    Append-only audit log entry.

    actor_user_id: the user who triggered the action (nullable for system events)
    entity_type / entity_id: the object the action was performed on
    action: short verb describing what happened
    metadata_json: safe, serialized context (no secrets)
    integrity_hash: SHA-256 of (actor + entity + action + timestamp + metadata)
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(TEXT, primary_key=True, default=uuid.uuid4)

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        TEXT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_label: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # human-readable actor (email/name) at time of event

    entity_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Safe serialized event metadata (no credentials, no secrets)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tamper-evidence
    integrity_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    actor_user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="audit_events"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} entity={self.entity_type}:{self.entity_id} "
            f"action={self.action!r}>"
        )
