"""
KaushalTwin Backend — Audit Service

Creates append-only AuditEvent records with cryptographic SHA-256 hash chaining in MongoDB.
Provides tamper detection, reordering detection, and full ledger integrity verification.
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

GENESIS_HASH = "0" * 64


def compute_event_hash(
    prev_hash: str,
    event_id: str,
    timestamp_str: str,
    actor_label: str,
    entity_type: str,
    entity_id: str,
    action: str,
    metadata_str: str,
) -> str:
    """Compute SHA-256 integrity hash with cryptographic linkage to previous event."""
    content = "|".join([
        prev_hash,
        event_id,
        timestamp_str,
        actor_label,
        entity_type,
        entity_id,
        action,
        metadata_str,
    ])
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_legacy_hash(
    actor_label: str,
    entity_type: str,
    entity_id: str,
    action: str,
    timestamp_str: str,
    metadata_str: str,
) -> str:
    """Compute legacy SHA-256 hash without hash chaining (for pre-existing records)."""
    content = "|".join([actor_label, entity_type, entity_id, action, timestamp_str, metadata_str])
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def record_event(
    db: AsyncIOMotorDatabase,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_user_id: Optional[uuid.UUID] = None,
    actor_label: Optional[str] = None,
    actor_role: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Create and persist an audit event in MongoDB linked into the hash chain.
    """
    now = datetime.now(timezone.utc)
    timestamp_str = now.isoformat()
    safe_label = actor_label or "system"
    safe_role = actor_role or "SYSTEM"
    safe_metadata = metadata or {}
    safe_metadata_str = json.dumps(safe_metadata, default=str, sort_keys=True)
    event_id = str(uuid.uuid4())

    # Find the latest event in the collection to link against
    prev_hash = GENESIS_HASH
    try:
        last_event = await db.audit_events.find_one(
            {},
            sort=[("timestamp", -1), ("_id", -1)],
        )
        if last_event and last_event.get("integrity_hash"):
            prev_hash = last_event["integrity_hash"]
    except Exception as exc:
        logger.warning("Could not retrieve latest audit event for chaining: %s", exc)

    integrity_hash = compute_event_hash(
        prev_hash=prev_hash,
        event_id=event_id,
        timestamp_str=timestamp_str,
        actor_label=safe_label,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        metadata_str=safe_metadata_str,
    )

    event_doc = {
        "id": event_id,
        "prev_hash": prev_hash,
        "integrity_hash": integrity_hash,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_label": safe_label,
        "actor_role": safe_role,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "action": action,
        "metadata_json": safe_metadata_str,
        "payload": safe_metadata,
        "timestamp": now,
        "timestamp_str": timestamp_str,
    }

    try:
        await db.audit_events.insert_one(event_doc)
        logger.debug("Audit event: %s %s:%s by %s (hash: %s...)", action, entity_type, entity_id, safe_label, integrity_hash[:8])
    except Exception as exc:
        logger.warning("Failed to record audit event: %s", exc)

    return event_doc


async def list_audit_events(
    db: AsyncIOMotorDatabase,
    *,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    """Retrieve audit events with filtering and pagination."""
    query: dict[str, Any] = {}
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"action": search_regex},
            {"entity_type": search_regex},
            {"entity_id": search_regex},
            {"actor_label": search_regex},
            {"actor_role": search_regex},
            {"metadata_json": search_regex},
        ]

    total = await db.audit_events.count_documents(query)
    cursor = db.audit_events.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    events: list[dict[str, Any]] = []
    async for doc in cursor:
        doc["_id"] = str(doc.get("_id"))
        if isinstance(doc.get("timestamp"), datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
        events.append(doc)
    return events, total


async def verify_audit_log_integrity(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    """
    Independently recomputes hashes and verifies chain links for all audit events.
    Detects modifications, deletions, and reordering.
    """
    cursor = db.audit_events.find({}).sort([("timestamp", 1), ("_id", 1)])
    events = await cursor.to_list(length=10000)

    if not events:
        return {
            "status": "EMPTY",
            "is_valid": True,
            "total_events": 0,
            "verified_events": 0,
            "corrupted_events": 0,
            "broken_links": 0,
            "errors": [],
            "guarantee": "SHA-256 Hash-Chain (Tamper-Evident)",
            "explanation": "No audit records found in database.",
        }

    expected_prev_hash: Optional[str] = None
    corrupted_count = 0
    broken_link_count = 0
    verified_count = 0
    errors: list[dict[str, Any]] = []

    for idx, evt in enumerate(events):
        evt_id = str(evt.get("id"))
        stored_hash = evt.get("integrity_hash", "")
        prev_hash = evt.get("prev_hash")
        actor_label = evt.get("actor_label", "system")
        entity_type = evt.get("entity_type", "")
        entity_id = str(evt.get("entity_id", ""))
        action = evt.get("action", "")
        metadata_str = evt.get("metadata_json") or json.dumps(evt.get("payload") or {}, default=str, sort_keys=True)
        
        # Determine timestamp string
        ts = evt.get("timestamp_str")
        if not ts:
            raw_ts = evt.get("timestamp")
            if isinstance(raw_ts, datetime):
                ts = raw_ts.isoformat()
            else:
                ts = str(raw_ts)

        is_chained = prev_hash is not None

        if is_chained:
            # Check previous hash relationship
            if expected_prev_hash is not None and prev_hash != expected_prev_hash:
                broken_link_count += 1
                errors.append({
                    "event_id": evt_id,
                    "index": idx,
                    "error_type": "BROKEN_CHAIN_LINK",
                    "expected_prev_hash": expected_prev_hash,
                    "actual_prev_hash": prev_hash,
                })

            # Check self-hash recomputation
            computed_hash = compute_event_hash(
                prev_hash=prev_hash,
                event_id=evt_id,
                timestamp_str=ts,
                actor_label=actor_label,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                metadata_str=metadata_str,
            )

            if computed_hash != stored_hash:
                corrupted_count += 1
                errors.append({
                    "event_id": evt_id,
                    "index": idx,
                    "error_type": "HASH_MISMATCH_TAMPERED",
                    "expected_hash": computed_hash,
                    "stored_hash": stored_hash,
                })
            else:
                verified_count += 1

            expected_prev_hash = stored_hash
        else:
            # Legacy event without chaining: check legacy hash formula
            legacy_hash = compute_legacy_hash(
                actor_label=actor_label,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                timestamp_str=ts,
                metadata_str=metadata_str,
            )
            if legacy_hash != stored_hash:
                # Some legacy events may have been formatted with different ts; test if valid
                corrupted_count += 1
                errors.append({
                    "event_id": evt_id,
                    "index": idx,
                    "error_type": "LEGACY_HASH_MISMATCH",
                    "stored_hash": stored_hash,
                })
            else:
                verified_count += 1
            # Next chained event may start chaining from this legacy event
            expected_prev_hash = stored_hash

    is_valid = (corrupted_count == 0 and broken_link_count == 0)
    status_str = "VERIFIED" if is_valid else "TAMPERED"

    return {
        "status": status_str,
        "is_valid": is_valid,
        "total_events": len(events),
        "verified_events": verified_count,
        "corrupted_events": corrupted_count,
        "broken_links": broken_link_count,
        "errors": errors[:20],  # cap to top 20 for payload size
        "guarantee": "SHA-256 Hash Chain (Tamper-Evident)",
        "explanation": (
            "Cryptographic hash chaining ensures that any modified event payload or broken link "
            "between chronological events is immediately detected by independent recomputation. "
            "Note: Application-level tamper-evidence proves ledger sequence integrity against API and application actors, "
            "but does not replace Write-Once-Read-Many (WORM) hardware storage against physical root database administrators."
        ),
    }
