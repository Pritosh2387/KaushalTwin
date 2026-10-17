"""
KaushalTwin Backend — FastAPI Application Entry Point

Unified Architecture:
    Frontend
        ↓
    Main Backend (FastAPI application — port 8000/8001)
        ├── Auth, Users, Workers, Evidence, Assessments, Decisions, Reports
        ├── MongoDB Database (Motor async driver)
        └── Embedded ML Service Layer (/api/v1/ml/...)
            ├── Transcript Preprocessing & Translation
            ├── Skill Extraction & NOS Semantic Mapping
            ├── Competency Twin Scoring & Skill Gap Engine
            ├── Evidence Verification & Multi-Modal Integrity
            ├── Adaptive Task Selector & Recommender
            ├── Abstention & Evidence Sufficiency Engine
            ├── Assessor Calibration & Consistency Analysis
            ├── Explainability & Audit Trail Generation
            └── Certification Recommendation & Structured Reports

Important:
- AI recommendations are strictly advisory; the certified human assessor retains final decision authority.
- The platform never autonomously certifies a candidate.
- All ML models and services are unified directly inside the backend.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection, mongo_manager, sanitize_mongodb_error
from app.api.v1 import api_router
from app.services.ml_client import init_ml_client, close_ml_client


# Embedded ML Routers
from ml.api.preprocessing import router as ml_preprocess_router
from ml.api.skills import router as ml_skills_router
from ml.api.competency import router as ml_competency_router
from ml.api.evidence import router as ml_evidence_router
from ml.api.assessment import router as ml_assessment_router
from ml.api.pipeline import router as ml_pipeline_router
from ml.api.skill_gap import router as ml_skill_gap_router
from ml.api.abstention import router as ml_abstention_router
from ml.api.calibration import router as ml_calibration_router
from ml.api.certification import router as ml_certification_router
from ml.api.explainability import router as ml_explainability_router
from ml.api.evaluation import router as ml_evaluation_router

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
    logger.info("Starting KaushalTwin Unified Backend (%s)", settings.APP_ENV)

    # Initialise MongoDB connection pool & ensure indexes
    await connect_to_mongo()

    # Auto-seed demo accounts in development or demo mode if database is empty
    if settings.is_development or settings.DEMO_MODE or settings.DEMO_DATA_ENABLED:
        try:
            from app.db.mongodb import mongo_manager
            if mongo_manager.db is not None:
                user_count = await mongo_manager.db.users.count_documents({})
                if user_count == 0:
                    logger.info("No users found in database. Seeding initial demo accounts...")
                    from seed_demo_data import seed
                    await seed()
        except Exception as seed_err:
            logger.debug("Demo data auto-seed check: %s", seed_err)

    # Initialise in-process ML client
    await init_ml_client(app)
    logger.info("Unified ML engine initialised in-process")

    yield  # Application runs here

    # Teardown
    await close_ml_client()
    await close_mongo_connection()
    logger.info("KaushalTwin Unified Backend stopped")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="KaushalTwin Backend API",
    description=(
        "Unified application backend for the KaushalTwin RPL platform.\n\n"
        "Provides authentication, worker management, assessment lifecycle, "
        "evidence management, embedded ML intelligence, assessor decisions, "
        "MongoDB persistence, audit trails, and report generation.\n\n"
        "**Important**: AI outputs are advisory only. "
        "The human assessor retains final decision authority. "
        "This service never autonomously certifies a worker."
    ),
    version="0.2.0",
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
# Core Backend Routers
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_PREFIX)

# ---------------------------------------------------------------------------
# Embedded ML Intelligence Routers (all mounted under /api/v1/ml)
# ---------------------------------------------------------------------------

ML_PREFIX = f"{settings.API_PREFIX}/ml"

app.include_router(ml_preprocess_router, prefix=ML_PREFIX)
app.include_router(ml_skills_router,     prefix=ML_PREFIX)
app.include_router(ml_competency_router, prefix=ML_PREFIX)
app.include_router(ml_evidence_router,   prefix=ML_PREFIX)
app.include_router(ml_assessment_router, prefix=ML_PREFIX)
app.include_router(ml_pipeline_router,   prefix=ML_PREFIX)
app.include_router(ml_skill_gap_router,  prefix=ML_PREFIX)
app.include_router(ml_abstention_router, prefix=ML_PREFIX)
app.include_router(ml_calibration_router, prefix=ML_PREFIX)
app.include_router(ml_certification_router, prefix=ML_PREFIX)
app.include_router(ml_explainability_router, prefix=ML_PREFIX)
app.include_router(ml_evaluation_router, prefix=ML_PREFIX)

# ---------------------------------------------------------------------------
# Genuine System Health Diagnostics
# ---------------------------------------------------------------------------

async def perform_system_health():
    """Execute live diagnostic tests on MongoDB and AI Engine without exposing secrets."""
    now = datetime.now(timezone.utc)
    db_status = "unavailable"
    db_latency_ms = None
    db_error = None

    # 1. Real MongoDB ping with timeout
    try:
        if mongo_manager.client is not None:
            t0 = time.perf_counter()
            await asyncio.wait_for(mongo_manager.client.admin.command("ping"), timeout=2.0)
            db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            db_status = "operational"
        else:
            db_error = "MongoDB client not initialized"
    except Exception as exc:
        db_status = "unavailable"
        db_error = sanitize_mongodb_error(exc, settings.MONGODB_URL)

    # 2. Real AI Competency Engine inspection
    ai_status = "operational"
    ai_details: dict = {}
    try:
        from ml.trade_registry import trade_registry
        from ml.services.skill_service import extract_skills

        trades = trade_registry.list_supported_trades()
        test_extraction = extract_skills("residential wiring MCB installation")
        ai_details = {
            "status": "operational",
            "provider_type": "in_process_semantic_and_rule_matching",
            "is_mock_llm": False,
            "supported_trades_count": len(trades),
            "smoke_test_extracted_skills_count": getattr(test_extraction, "count", len(getattr(test_extraction, "skills", []))),
            "pipeline_ready": True,
        }
    except Exception as exc:
        ai_status = "degraded"
        ai_details = {
            "status": "degraded",
            "provider_type": "in_process_semantic_and_rule_matching",
            "error": str(exc),
            "pipeline_ready": False,
        }

    # Overall service status
    if db_status == "operational" and ai_status == "operational":
        overall_status = "operational"
    elif db_status == "operational" or ai_status == "operational":
        overall_status = "degraded"
    else:
        overall_status = "unavailable"

    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "version": "0.2.0",
        "env": settings.APP_ENV,
        "timestamp": now.isoformat(),
        "dependencies": {
            "fastapi": {
                "status": "operational",
                "service": "FastAPI Application",
            },
            "mongodb": {
                "status": db_status,
                "driver": "Motor Async Driver",
                "database": settings.MONGODB_DB_NAME,
                "latency_ms": db_latency_ms,
                "error": db_error,
            },
            "ai_competency_engine": ai_details,
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    return await perform_system_health()


@app.get(f"{settings.API_PREFIX}/health", tags=["Health"])
async def api_health():
    return await perform_system_health()


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": settings.APP_NAME,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": settings.API_PREFIX,
        "ml_prefix": ML_PREFIX,
    }

