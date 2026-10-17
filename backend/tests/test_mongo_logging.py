"""
KaushalTwin Backend — Focused Tests for MongoDB Credential Scrubbing & Log Security

Verifies that MongoDB connection logging, error handling, and target descriptions
never expose raw database URIs, usernames, passwords, or authentication parameters.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.db.mongodb import (
    connect_to_mongo,
    ensure_indexes,
    get_safe_mongodb_target,
    mongo_manager,
    sanitize_mongodb_error,
)


DUMMY_ATLAS_USER = "sih_atlas_user"
DUMMY_ATLAS_PASS = "Super$ecretP@ssw0rd!123"
DUMMY_ATLAS_PASS_ENCODED = "Super%24ecretP%40ssw0rd%21123"
DUMMY_ATLAS_HOST = "cluster0.abcde.mongodb.net"
DUMMY_ATLAS_URL = (
    f"mongodb+srv://{DUMMY_ATLAS_USER}:{DUMMY_ATLAS_PASS_ENCODED}@"
    f"{DUMMY_ATLAS_HOST}/kaushaltwin?retryWrites=true&w=majority&authSource=admin"
)

DUMMY_STANDALONE_USER = "prod_mongo_admin"
DUMMY_STANDALONE_PASS = "ExtremelyPrivate123"
DUMMY_STANDALONE_HOST = "prod-mongo-primary.internal.cloud:27017"
DUMMY_STANDALONE_URL = (
    f"mongodb://{DUMMY_STANDALONE_USER}:{DUMMY_STANDALONE_PASS}@"
    f"{DUMMY_STANDALONE_HOST}/kaushaltwin?authSource=admin"
)


class TestMongoTargetSanitization:
    """Tests for get_safe_mongodb_target ensuring credentials are never returned."""

    def test_atlas_uri_target_sanitization(self):
        target = get_safe_mongodb_target(DUMMY_ATLAS_URL)
        assert DUMMY_ATLAS_USER not in target
        assert DUMMY_ATLAS_PASS not in target
        assert DUMMY_ATLAS_PASS_ENCODED not in target
        assert "mongodb+srv://" not in target
        assert "authSource" not in target
        assert "retryWrites" not in target
        assert DUMMY_ATLAS_HOST in target
        assert target == f"configured MongoDB Atlas deployment ({DUMMY_ATLAS_HOST})"

    def test_standalone_uri_target_sanitization(self):
        target = get_safe_mongodb_target(DUMMY_STANDALONE_URL)
        assert DUMMY_STANDALONE_USER not in target
        assert DUMMY_STANDALONE_PASS not in target
        assert "mongodb://" not in target
        assert "authSource" not in target
        assert DUMMY_STANDALONE_HOST in target
        assert target == f"configured MongoDB deployment ({DUMMY_STANDALONE_HOST})"

    def test_localhost_uri_target(self):
        target = get_safe_mongodb_target("mongodb://dev_user:dev_pass@localhost:27017")
        assert "dev_user" not in target
        assert "dev_pass" not in target
        assert target == "local MongoDB deployment (localhost:27017)"

    def test_empty_or_none_uri_target(self):
        assert get_safe_mongodb_target(None) == "unconfigured MongoDB deployment"
        assert get_safe_mongodb_target("") == "unconfigured MongoDB deployment"


class TestMongoErrorSanitization:
    """Tests for sanitize_mongodb_error ensuring error strings never leak secrets."""

    def test_scrubs_raw_url_and_credentials_from_exception_message(self):
        leaky_msg = (
            f"ServerSelectionTimeoutError: Failed to connect to {DUMMY_ATLAS_URL}: "
            f"Authentication failed for user '{DUMMY_ATLAS_USER}' with password '{DUMMY_ATLAS_PASS}'"
        )
        sanitized = sanitize_mongodb_error(leaky_msg, DUMMY_ATLAS_URL)

        assert DUMMY_ATLAS_USER not in sanitized
        assert DUMMY_ATLAS_PASS not in sanitized
        assert DUMMY_ATLAS_PASS_ENCODED not in sanitized
        assert DUMMY_ATLAS_URL not in sanitized
        assert "authSource" not in sanitized
        assert "[MASKED_MONGODB_URI]" in sanitized

    def test_generic_scrub_without_known_raw_url(self):
        leaky_msg = "Could not reach mongodb://secret_admin:VerySecretPass999@10.0.0.5:27017/app_db?authSource=admin"
        sanitized = sanitize_mongodb_error(leaky_msg)

        assert "secret_admin" not in sanitized
        assert "VerySecretPass999" not in sanitized
        assert "mongodb://" not in sanitized
        assert "[MASKED_MONGODB_URI]" in sanitized

    def test_empty_error_returns_empty_string(self):
        assert sanitize_mongodb_error(None) == ""
        assert sanitize_mongodb_error("") == ""


class TestMongoConnectionLogging:
    """Tests verifying logger output during connect_to_mongo and index creation."""

    @pytest.mark.asyncio
    async def test_connect_to_mongo_logs_safe_target_without_credentials(self, caplog):
        caplog.set_level(logging.INFO, logger="app.db.mongodb")

        mock_db = MagicMock()
        mock_db.users.create_index = AsyncMock()
        mock_db.workers.create_index = AsyncMock()
        mock_db.evidence.create_index = AsyncMock()
        mock_db.assessments.create_index = AsyncMock()
        mock_db.assessment_tasks.create_index = AsyncMock()
        mock_db.ai_runs.create_index = AsyncMock()
        mock_db.decisions.create_index = AsyncMock()
        mock_db.audit_events.create_index = AsyncMock()

        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})

        with patch("app.db.mongodb.settings") as mock_settings, \
             patch("app.db.mongodb.AsyncIOMotorClient", return_value=mock_client):
            mock_settings.MONGODB_URL = DUMMY_ATLAS_URL
            mock_settings.MONGODB_DB_NAME = "kaushaltwin"

            await connect_to_mongo()

            log_output = caplog.text
            # Strictly verify credentials never appear anywhere in logs
            assert DUMMY_ATLAS_USER not in log_output
            assert DUMMY_ATLAS_PASS not in log_output
            assert DUMMY_ATLAS_PASS_ENCODED not in log_output
            assert "mongodb+srv://" not in log_output
            assert "authSource" not in log_output
            assert "retryWrites" not in log_output

            # Verify safe target message was logged
            assert f"Connecting to configured MongoDB Atlas deployment ({DUMMY_ATLAS_HOST})" in log_output
            assert "Successfully connected to MongoDB database 'kaushaltwin'" in log_output

    @pytest.mark.asyncio
    async def test_connect_to_mongo_ping_failure_does_not_leak_credentials(self, caplog):
        caplog.set_level(logging.WARNING, logger="app.db.mongodb")

        mock_db = MagicMock()
        mock_db.users.create_index = AsyncMock()
        mock_db.workers.create_index = AsyncMock()
        mock_db.evidence.create_index = AsyncMock()
        mock_db.assessments.create_index = AsyncMock()
        mock_db.assessment_tasks.create_index = AsyncMock()
        mock_db.ai_runs.create_index = AsyncMock()
        mock_db.decisions.create_index = AsyncMock()
        mock_db.audit_events.create_index = AsyncMock()

        mock_client = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        # Simulate a ping failure that embeds connection credentials in exception
        mock_client.admin.command = AsyncMock(
            side_effect=RuntimeError(
                f"Connection failure to {DUMMY_ATLAS_URL} for user {DUMMY_ATLAS_USER}: timeout"
            )
        )

        with patch("app.db.mongodb.settings") as mock_settings, \
             patch("app.db.mongodb.AsyncIOMotorClient", return_value=mock_client):
            mock_settings.MONGODB_URL = DUMMY_ATLAS_URL
            mock_settings.MONGODB_DB_NAME = "kaushaltwin"

            await connect_to_mongo()

            log_output = caplog.text
            assert DUMMY_ATLAS_USER not in log_output
            assert DUMMY_ATLAS_PASS not in log_output
            assert DUMMY_ATLAS_PASS_ENCODED not in log_output
            assert DUMMY_ATLAS_URL not in log_output
            assert "Could not ping MongoDB:" in log_output

    @pytest.mark.asyncio
    async def test_ensure_indexes_failure_does_not_leak_credentials(self, caplog):
        caplog.set_level(logging.WARNING, logger="app.db.mongodb")

        mock_db = MagicMock()
        mock_db.users.create_index = AsyncMock(
            side_effect=RuntimeError(
                f"Index error on {DUMMY_STANDALONE_URL} for user {DUMMY_STANDALONE_USER}"
            )
        )

        with patch("app.db.mongodb.settings") as mock_settings:
            mock_settings.MONGODB_URL = DUMMY_STANDALONE_URL

            await ensure_indexes(mock_db)

            log_output = caplog.text
            assert DUMMY_STANDALONE_USER not in log_output
            assert DUMMY_STANDALONE_PASS not in log_output
            assert DUMMY_STANDALONE_URL not in log_output
            assert "Error creating MongoDB indexes:" in log_output
