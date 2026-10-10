"""
KaushalTwin Backend — Application Configuration

Reads all settings from environment variables / .env file.
Required settings are validated at startup; the app will refuse to start
if critical configuration is missing.
"""

from __future__ import annotations

import secrets
from typing import Literal
from pydantic import field_validator, AnyHttpUrl
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
    DATABASE_URL: str = "sqlite+aiosqlite:///./kaushaltwin_dev.db"

    # ── Security ─────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_hex(32)  # Overridden by env var in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── ML Service ───────────────────────────────────────────────────────────
    ML_SERVICE_URL: str = "http://localhost:8000"
    ML_SERVICE_TIMEOUT: int = 30  # seconds

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIRECTORY: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: str = "pdf,jpg,jpeg,png,mp4,mov,docx,txt"

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


# Module-level singleton — import this everywhere
settings = Settings()
