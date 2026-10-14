"""
KaushalTwin Backend — Application Configuration

Reads all settings from environment variables / .env file.
Required settings are validated at startup; the app will refuse to start
if critical configuration is missing.
"""

from __future__ import annotations

import secrets
from typing import Literal, Optional
from pydantic import field_validator, AnyHttpUrl, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "testing", "production"] = "development"
    APP_NAME: str = "KaushalTwin Backend"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "kaushaltwin"
    DATABASE_URL: str = "sqlite+aiosqlite:///./kaushaltwin_dev.db"

    # ── Security ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_hex(32)  # Overridden by env var in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── ML Providers Configuration ───────────────────────────────────────────
    # Skill Extraction Provider
    SKILL_EXTRACTION_PROVIDER: Literal["demo", "llm"] = "demo"
    LLM_SKILL_API_KEY: Optional[str] = None
    LLM_SKILL_MODEL: str = "gpt-4o-mini"

    # Embedding Provider
    EMBEDDING_PROVIDER: Literal["demo", "sentence_transformer"] = "demo"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 64

    # Speech-to-Text Provider
    STT_PROVIDER: Literal["mock", "whisper"] = "mock"
    WHISPER_MODEL_SIZE: str = "base"

    # ML Service (for external ML service calls)
    ML_SERVICE_URL: str = "http://localhost:8000"
    ML_SERVICE_TIMEOUT: int = 30  # seconds

    # Demo Mode Configuration
    DEMO_MODE: bool = False
    DEMO_DATA_ENABLED: bool = False

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173"

    # ── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,mp4,mov,docx,txt"

    # ── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("APP_ENV") == "production":
            if not v or v == "CHANGE_ME_generate_a_real_secret_key" or len(v) < 32:
                raise ValueError("JWT_SECRET_KEY must be set to a strong secret in production (minimum 32 characters)")
        return v

    @field_validator("MONGODB_URL")
    @classmethod
    def validate_mongodb_url(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("APP_ENV") == "production":
            if not v or v == "mongodb://localhost:27017":
                raise ValueError("MONGODB_URL must be configured for production use")
        return v

    @field_validator("ML_SERVICE_URL")
    @classmethod
    def validate_ml_service_url(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("APP_ENV") == "production":
            if not v or v == "http://localhost:8000":
                raise ValueError("ML_SERVICE_URL must be configured for production use")
        return v

    @field_validator("CORS_ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str, info: ValidationInfo) -> str:
        if info.data.get("APP_ENV") == "production":
            origins = [o.strip() for o in v.split(",") if o.strip()]
            for origin in origins:
                if not origin.startswith(("http://", "https://")):
                    raise ValueError(f"CORS origin '{origin}' must be a valid URL starting with http:// or https://")
                if "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError(f"CORS origin '{origin}' should not contain localhost in production")
        return v

    @field_validator("DEMO_MODE")
    @classmethod
    def validate_demo_mode(cls, v: bool, info: ValidationInfo) -> bool:
        if info.data.get("APP_ENV") == "production" and v:
            raise ValueError("DEMO_MODE must be disabled in production")
        return v

    @field_validator("DEMO_DATA_ENABLED")
    @classmethod
    def validate_demo_data(cls, v: bool, info: ValidationInfo) -> bool:
        if info.data.get("APP_ENV") == "production" and v:
            raise ValueError("DEMO_DATA_ENABLED must be disabled in production")
        return v

    # ── Computed properties ───────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",") if e.strip()}

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def uses_demo_skill_provider(self) -> bool:
        return self.SKILL_EXTRACTION_PROVIDER == "demo" or (self.SKILL_EXTRACTION_PROVIDER == "llm" and not self.LLM_SKILL_API_KEY)

    @property
    def uses_demo_embedding_provider(self) -> bool:
        return self.EMBEDDING_PROVIDER == "demo"


# Module-level singleton — import this everywhere
settings = Settings()
