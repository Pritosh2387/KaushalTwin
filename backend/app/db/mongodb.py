"""
KaushalTwin Backend — MongoDB Client and Lifecycle Management

Provides asynchronous MongoDB connection management using Motor, collection accessors,
and automatic index creation for all collections.
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Union
from urllib.parse import quote_plus, unquote
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_safe_mongodb_target(raw_url: Optional[str] = None) -> str:
    """
    Extract a safe description of the MongoDB deployment target without exposing
    credentials, auth parameters, or the raw connection string.
    """
    if not raw_url:
        return "unconfigured MongoDB deployment"
    try:
        # Match mongodb or mongodb+srv URI authority part
        match = re.search(r"mongodb(?:\+srv)?://(?:[^@/]+@)?([^/?#]+)", raw_url)
        if match:
            hosts = match.group(1).strip()
            is_srv = raw_url.startswith("mongodb+srv://")
            is_atlas = "mongodb.net" in hosts.lower() or is_srv
            if is_atlas:
                return f"configured MongoDB Atlas deployment ({hosts})"
            if "localhost" in hosts or "127.0.0.1" in hosts:
                return f"local MongoDB deployment ({hosts})"
            return f"configured MongoDB deployment ({hosts})"
    except Exception:
        pass
    return "configured MongoDB deployment"


def sanitize_mongodb_error(error: Union[Exception, str, None], raw_url: Optional[str] = None) -> str:
    """
    Scrub connection strings, credentials, and sensitive authentication parameters from error messages.
    """
    msg = str(error) if error is not None else ""
    if not msg:
        return ""

    if raw_url:
        try:
            # Extract and scrub credentials from the known raw_url
            cred_match = re.search(r"mongodb(?:\+srv)?://([^/@]+)@", raw_url)
            if cred_match:
                userinfo = cred_match.group(1)
                for part in userinfo.split(":", 1):
                    if part and len(part) > 1:
                        msg = msg.replace(part, "***")
                        unquoted = unquote(part)
                        if unquoted != part and len(unquoted) > 1:
                            msg = msg.replace(unquoted, "***")
                        quoted = quote_plus(unquoted)
                        if quoted != part and len(quoted) > 1:
                            msg = msg.replace(quoted, "***")
            msg = msg.replace(raw_url, "[MASKED_MONGODB_URI]")
        except Exception:
            pass

    # Generic scrub: replace any mongodb:// or mongodb+srv:// URI with a safe placeholder
    msg = re.sub(
        r"mongodb(?:\+srv)?://[^\s'\"<>,;)]+",
        "[MASKED_MONGODB_URI]",
        msg,
    )

    # Generic scrub: replace any residual user:password@ authority formats
    msg = re.sub(r"://([^:@/\s]+):([^@/\s]+)@", r"://***:***@", msg)

    # Generic scrub: mask sensitive auth parameters in query strings
    msg = re.sub(r"(authSource|authMechanism|gssapiServiceName)=[^&;\s]+", r"\1=***", msg)

    return msg


class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongo_manager = MongoDBManager()


async def connect_to_mongo() -> AsyncIOMotorDatabase:
    """Connect to MongoDB and ensure indexes exist."""
    logger.info("Connecting to %s", get_safe_mongodb_target(settings.MONGODB_URL))
    try:
        mongo_manager.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard",
        )
        mongo_manager.db = mongo_manager.client[settings.MONGODB_DB_NAME]
    except Exception as exc:
        logger.error("Failed to initialize MongoDB client: %s", sanitize_mongodb_error(exc, settings.MONGODB_URL))
        raise
    
    # Verify connection
    try:
        await mongo_manager.client.admin.command("ping")
        logger.info("Successfully connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)
    except Exception as exc:
        logger.warning("Could not ping MongoDB: %s", sanitize_mongodb_error(exc, settings.MONGODB_URL))

    # Ensure indexes
    await ensure_indexes(mongo_manager.db)
    return mongo_manager.db


async def close_mongo_connection() -> None:
    """Close the MongoDB connection pool."""
    if mongo_manager.client is not None:
        mongo_manager.client.close()
        mongo_manager.client = None
        mongo_manager.db = None
        logger.info("Closed MongoDB connection pool")


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create essential indexes on collections."""
    try:
        # Users
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)

        # Worker profiles
        await db.workers.create_index("id", unique=True)
        await db.workers.create_index("user_id")

        # Evidence
        await db.evidence.create_index("id", unique=True)
        await db.evidence.create_index("worker_id")

        # Assessments
        await db.assessments.create_index("id", unique=True)
        await db.assessments.create_index("worker_id")
        await db.assessments.create_index("assessor_id")

        # Assessment Tasks
        await db.assessment_tasks.create_index("id", unique=True)
        await db.assessment_tasks.create_index("assessment_id")

        # AI Runs
        await db.ai_runs.create_index("id", unique=True)
        await db.ai_runs.create_index("assessment_id")

        # Decisions
        await db.decisions.create_index("id", unique=True)
        await db.decisions.create_index("assessment_id")

        # Audit events
        await db.audit_events.create_index("id", unique=True)
        await db.audit_events.create_index([("entity_type", 1), ("entity_id", 1)])
        await db.audit_events.create_index("timestamp")
        logger.info("MongoDB indexes verified/created")
    except Exception as exc:
        logger.warning("Error creating MongoDB indexes: %s", sanitize_mongodb_error(exc, settings.MONGODB_URL))


def get_database() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database instance."""
    if mongo_manager.db is None:
        raise RuntimeError("MongoDB connection is not initialised. Call connect_to_mongo() first.")
    return mongo_manager.db
