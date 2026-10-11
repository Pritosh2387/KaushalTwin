"""
KaushalTwin Backend — Audit Service

Creates append-only AuditEvent records with SHA-256 integrity hashes in MongoDB.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

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
    db: AsyncIOMotorDatabase,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_label: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Create and persist an audit event in MongoDB.
    """
    now = datetime.now(timezone.utc)
    timestamp_str = now.isoformat()
    safe_label = actor_label or "system"
    safe_metadata_str = json.dumps(metadata or {}, default=str, sort_keys=True)

    integrity_hash = _compute_hash(
        safe_label, entity_type, entity_id, action, timestamp_str, safe_metadata_str
    )

    event_id = str(uuid.uuid4())
    event_doc = {
        "id": event_id,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_label": safe_label,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "action": action,
        "metadata_json": safe_metadata_str,
        "payload": metadata or {},
        "integrity_hash": integrity_hash,
        "timestamp": now,
    }

    try:
        await db.audit_events.insert_one(event_doc)
        logger.debug("Audit event: %s %s:%s by %s", action, entity_type, entity_id, safe_label)
    except Exception as exc:
        logger.warning("Failed to record audit event: %s", exc)

    return event_doc
