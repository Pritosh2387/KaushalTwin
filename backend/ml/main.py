"""
KaushalTwin ML Service — FastAPI Application Entry Point
"""

from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ml.api.preprocessing import router as preprocess_router
from ml.api.skills import router as skills_router
from ml.api.competency import router as competency_router
from ml.api.evidence import router as evidence_router
from ml.api.assessment import router as assessment_router
from ml.api.pipeline import router as pipeline_router
from ml.api.skill_gap import router as skill_gap_router
from ml.api.abstention import router as abstention_router
from ml.api.calibration import router as calibration_router
from ml.api.certification import router as certification_router
from ml.api.explainability import router as explainability_router

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="KaushalTwin ML Service",
    description=(
        "AI/ML intelligence layer for the KaushalTwin RPL platform.\n\n"
        "Provides:\n"
        "- transcript preprocessing\n"
        "- skill extraction\n"
        "- NOS mapping\n"
        "- Competency Twin scoring\n"
        "- evidence analysis and integrity\n"
        "- adaptive assessment task selection\n"
        "- skill-gap and evidence-debt analysis\n"
        "- evidence sufficiency and abstention recommendations\n"
        "- assessor calibration and consistency analysis\n"
        "- competency profiling\n"
        "- certification recommendations\n"
        "- explainability and audit trails\n"
        "- assessor-facing decision reports\n\n"
        "IMPORTANT:\n"
        "This service assists human assessors.\n"
        "It never independently certifies a worker.\n"
        "It never makes the final assessor decision.\n"
        "Abstention and certification outputs are AI recommendations only.\n"
        "The human assessor retains final authority.\n"
    ),
    version="0.1.0",
    contact={"name": "KaushalTwin Team", "email": "team@kaushaltwin.example"},
    license_info={"name": "MIT"},
)

# ---------------------------------------------------------------------------
# CORS (open for demo; restrict in production)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc),
                "details": {},
            }
        },
    )

# ---------------------------------------------------------------------------
# Routers — all under /api/v1/ml/
# ---------------------------------------------------------------------------

PREFIX = "/api/v1/ml"

app.include_router(preprocess_router, prefix=PREFIX)
app.include_router(skills_router,     prefix=PREFIX)
app.include_router(competency_router, prefix=PREFIX)
app.include_router(evidence_router,   prefix=PREFIX)
app.include_router(assessment_router, prefix=PREFIX)
app.include_router(pipeline_router,   prefix=PREFIX)
app.include_router(skill_gap_router,  prefix=PREFIX)
app.include_router(abstention_router, prefix=PREFIX)
app.include_router(calibration_router, prefix=PREFIX)
app.include_router(certification_router, prefix=PREFIX)
app.include_router(explainability_router, prefix=PREFIX)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():
    """Service liveness check."""
    return {"status": "ok", "service": "KaushalTwin ML Service", "version": "0.1.0"}


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "KaushalTwin ML Service",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }