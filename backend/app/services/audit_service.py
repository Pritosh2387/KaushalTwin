"""
KaushalTwin Backend — Audit Service

Creates append-only AuditEvent records with SHA-256 integrity hashes.
Callers should use this service rather than inserting AuditEvent rows directly.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditEvent

logger = logging.getLogger(__name__)


def _compute_hash(
    actor_label: str,
    entity_type: str,
    entity_id: str,
    action: str,
    timestamp: str,
    metadata: str,
) -> str:
    content = "|".join([actor_label, entity_type, entity_id, action, timestamp, metadata])
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def record_event(
    db: AsyncSession,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_label: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    """
    Create and persist an audit event.

    :param action:       Short verb, e.g. 'ASSESSMENT_CREATED', 'ML_RUN_COMPLETED'
    :param entity_type:  Model name, e.g. 'Assessment', 'EvidenceRecord'
    :param entity_id:    The entity's UUID as string
    :param actor_user_id: User who triggered the action (None for system events)
    :param actor_label:  Human-readable actor label at the time of the event
    :param metadata:     Safe, non-secret context dict
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_label = actor_label or "system"
    safe_metadata_str = json.dumps(metadata or {}, default=str, sort_keys=True)

    integrity_hash = _compute_hash(
        safe_label, entity_type, entity_id, action, timestamp, safe_metadata_str
    )

    event = AuditEvent(
        id=uuid.uuid4(),
        actor_user_id=actor_user_id,
        actor_label=safe_label,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        metadata_json=safe_metadata_str,
        integrity_hash=integrity_hash,
    )
    db.add(event)
    # Note: session commit is handled by the get_db_session generator
    logger.debug("Audit event: %s %s:%s by %s", action, entity_type, entity_id, safe_label)
    return event
