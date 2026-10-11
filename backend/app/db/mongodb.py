"""
KaushalTwin Backend — MongoDB Client and Lifecycle Management

Provides asynchronous MongoDB connection management using Motor, collection accessors,
and automatic index creation for all collections.
"""

from __future__ import annotations

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongo_manager = MongoDBManager()


async def connect_to_mongo() -> AsyncIOMotorDatabase:
    """Connect to MongoDB and ensure indexes exist."""
    logger.info("Connecting to MongoDB at %s", settings.MONGODB_URL)
    mongo_manager.client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        uuidRepresentation="standard",
    )
    mongo_manager.db = mongo_manager.client[settings.MONGODB_DB_NAME]
    
    # Verify connection
    try:
        await mongo_manager.client.admin.command("ping")
        logger.info("Successfully connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)
    except Exception as exc:
        logger.warning("Could not ping MongoDB: %s", exc)

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
        logger.warning("Error creating MongoDB indexes: %s", exc)


def get_database() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database instance."""
    if mongo_manager.db is None:
        raise RuntimeError("MongoDB connection is not initialised. Call connect_to_mongo() first.")
    return mongo_manager.db
