"""
Configuration management tests for KaushalTwin Backend.
Tests environment-specific configuration, validation, and provider selection.
"""

import os
import sys
from pathlib import Path

# Add current directory to path so we can import app modules
sys.path.insert(0, ".")

import pytest
from pydantic import ValidationError
from app.core.config import Settings


def get_clean_settings(**env_vars):
    """Create a fresh settings instance with only the specified environment variables."""
    # Save original environment
    original_env = dict(os.environ)

    try:
        # Clear relevant environment variables
        for key in list(os.environ.keys()):
            if key.startswith(('APP_', 'JWT_', 'MONGODB_', 'ML_', 'CORS_', 'SKILL_', 'EMBEDDING_', 'STT_', 'DEMO_', 'UPLOAD_', 'MAX_', 'ALLOWED_', 'LOG_')):
                del os.environ[key]

        # Set only the specified environment variables
        for key, value in env_vars.items():
            os.environ[key] = value

        # Create fresh settings instance
        return Settings(_env_file=None)
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


def test_development_config():
    """Test development environment configuration."""
    settings = get_clean_settings(APP_ENV="development")

    assert settings.APP_ENV == "development"
    assert settings.DEBUG == False  # Default value
    assert settings.DEMO_MODE == False  # Default
    assert settings.uses_demo_skill_provider == True  # Default provider is demo
    assert settings.uses_demo_embedding_provider == True  # Default provider is demo


def test_testing_config():
    """Test testing environment configuration."""
    settings = get_clean_settings(APP_ENV="testing")

    assert settings.APP_ENV == "testing"
    assert settings.is_testing == True


def test_production_config_validation():
    """Test production environment validation."""
    settings = get_clean_settings(
        APP_ENV="production",
        JWT_SECRET_KEY="production_secret_key_12345678901234567890",  # 40 chars
        MONGODB_URL="mongodb://production-host:27017",
        ML_SERVICE_URL="https://ml.production.example.com",
        CORS_ALLOWED_ORIGINS="https://frontend.production.example.com"
    )

    assert settings.APP_ENV == "production"
    assert settings.JWT_SECRET_KEY == "production_secret_key_12345678901234567890"
    assert settings.MONGODB_URL == "mongodb://production-host:27017"
    assert settings.ML_SERVICE_URL == "https://ml.production.example.com"
    assert settings.is_production == True

    # Demo mode should be False in production (validated)
    assert settings.DEMO_MODE == False


def test_production_config_missing_jwt_secret():
    """Test that production rejects weak JWT secret."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY must be set to a strong secret in production"):
        get_clean_settings(
            APP_ENV="production",
            JWT_SECRET_KEY="weak_key",  # Too short
            MONGODB_URL="mongodb://production-host:27017",
            ML_SERVICE_URL="https://ml.production.example.com"
        )


def test_production_config_localhost_cors():
    """Test that production rejects localhost in CORS origins."""
    with pytest.raises(ValidationError, match="CORS origin.*should not contain localhost in production"):
        get_clean_settings(
            APP_ENV="production",
            JWT_SECRET_KEY="production_secret_key_12345678901234567890",
            MONGODB_URL="mongodb://production-host:27017",
            ML_SERVICE_URL="https://ml.production.example.com",
            CORS_ALLOWED_ORIGINS="http://localhost:3000"
        )


def test_production_config_demo_mode_disabled():
    """Test that production rejects demo mode enabled."""
    with pytest.raises(ValidationError, match="DEMO_MODE must be disabled in production"):
        get_clean_settings(
            APP_ENV="production",
            JWT_SECRET_KEY="production_secret_key_12345678901234567890",
            MONGODB_URL="mongodb://production-host:27017",
            ML_SERVICE_URL="https://ml.production.example.com",
            DEMO_MODE="true"
        )


def test_llm_skill_provider_selection():
    """Test LLM skill provider selection when API key is provided."""
    settings = get_clean_settings(
        APP_ENV="development",
        SKILL_EXTRACTION_PROVIDER="llm",
        LLM_SKILL_API_KEY="test-api-key"
    )

    assert settings.SKILL_EXTRACTION_PROVIDER == "llm"
    assert settings.LLM_SKILL_API_KEY == "test-api-key"
    assert settings.uses_demo_skill_provider == False  # Should use LLM when API key provided


def test_llm_skill_provider_fallback_to_demo():
    """Test that LLM provider falls back to demo when no API key."""
    settings = get_clean_settings(
        APP_ENV="development",
        SKILL_EXTRACTION_PROVIDER="llm"
        # LLM_SKILL_API_KEY not set - should fall back to demo
    )

    assert settings.SKILL_EXTRACTION_PROVIDER == "llm"
    assert settings.LLM_SKILL_API_KEY is None
    assert settings.uses_demo_skill_provider == True  # Should fall back to demo


def test_sentence_transformer_embedding_provider():
    """Test sentence transformer embedding provider selection."""
    settings = get_clean_settings(
        APP_ENV="development",
        EMBEDDING_PROVIDER="sentence_transformer"
    )

    assert settings.EMBEDDING_PROVIDER == "sentence_transformer"
    assert settings.uses_demo_embedding_provider == False


def test_environment_property_methods():
    """Test environment property helper methods."""
    # Test development
    settings = get_clean_settings(APP_ENV="development")
    assert settings.is_development == True
    assert settings.is_testing == False
    assert settings.is_production == False

    # Test testing
    settings = get_clean_settings(APP_ENV="testing")
    assert settings.is_development == False
    assert settings.is_testing == True
    assert settings.is_production == False

    # Test production - need to provide valid production values to avoid validation errors
    settings = get_clean_settings(
        APP_ENV="production",
        JWT_SECRET_KEY="production_secret_key_12345678901234567890",
        MONGODB_URL="mongodb://production-host:27017",
        ML_SERVICE_URL="https://ml.production.example.com",
        CORS_ALLOWED_ORIGINS="https://frontend.production.example.com"
    )
    assert settings.is_development == False
    assert settings.is_testing == False
    assert settings.is_production == True


def test_cors_origins_list():
    """Test CORS origins list parsing."""
    settings = get_clean_settings(
        CORS_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173,https://example.com"
    )

    expected = ["http://localhost:3000", "http://localhost:5173", "https://example.com"]
    assert settings.cors_origins_list == expected


def test_allowed_extensions_set():
    """Test allowed extensions set parsing."""
    settings = get_clean_settings(
        ALLOWED_EXTENSIONS="pdf,jpg,jpeg,png,mp4,mov,docx,txt"
    )

    expected = {"pdf", "jpg", "jpeg", "png", "mp4", "mov", "docx", "txt"}
    assert settings.allowed_extensions_set == expected


def test_demo_mode_development_allowed():
    """Test that demo mode is allowed in development."""
    settings = get_clean_settings(
        APP_ENV="development",
        DEMO_MODE="true",
        DEMO_DATA_ENABLED="true"
    )

    assert settings.DEMO_MODE == True
    assert settings.DEMO_DATA_ENABLED == True


def test_demo_data_development_allowed():
    """Test that demo data is allowed in development."""
    settings = get_clean_settings(
        APP_ENV="development",
        DEMO_DATA_ENABLED="true"
    )

    assert settings.DEMO_DATA_ENABLED == True