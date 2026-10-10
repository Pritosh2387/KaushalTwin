"""
KaushalTwin Backend — FastAPI Application Entry Point

Architecture:
    Frontend
        ↓
    Main Backend (this service — port 8001 by default)
        ├── Auth, Users, Workers, Evidence, Assessments, Decisions, Reports
        ├── SQLite/PostgreSQL (persistent state)
        └── ML Service Client (calls ml_service on port 8000)
                ↓
        KaushalTwin ML Service (existing, port 8000)

Important:
- This service never auto-certifies a worker.
- All AI outputs are advisory; the human assessor makes the final decision.
- The ML service is stateless; all persistence is handled here.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.services.ml_client import init_ml_client, close_ml_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup; clean up on shutdown."""
    logger.info("Starting KaushalTwin Backend (%s)", settings.APP_ENV)

    # Initialise the ML service HTTP client
    await init_ml_client()
    logger.info("ML service URL: %s", settings.ML_SERVICE_URL)

    yield  # Application runs here

    # Teardown
    await close_ml_client()
    logger.info("KaushalTwin Backend stopped")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="KaushalTwin Backend API",
    description=(
        "Main application backend for the KaushalTwin RPL platform.\n\n"
        "Provides authentication, worker management, assessment lifecycle, "
        "evidence management, ML service integration, assessor decisions, "
        "audit trails, and report generation.\n\n"
        "**Important**: AI outputs are advisory only. "
        "The human assessor retains final decision authority. "
        "This service never autonomously certifies a worker."
    ),
    version="0.1.0",
    contact={"name": "KaushalTwin Team"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler — never exposes stack traces or env variables to clients."""
    logger.exception("Unhandled exception: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_PREFIX)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    """Backend liveness check."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "env": settings.APP_ENV,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": settings.API_PREFIX,
    }
