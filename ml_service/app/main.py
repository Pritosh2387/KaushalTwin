"""
KaushalTwin ML Service — FastAPI Application Entry Point
"""

from __future__ import annotations

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.preprocessing import router as preprocess_router
from app.api.skills import router as skills_router
from app.api.competency import router as competency_router
from app.api.evidence import router as evidence_router
from app.api.assessment import router as assessment_router
from app.api.pipeline import router as pipeline_router

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="KaushalTwin ML Service",
    description=(
        "AI/ML intelligence layer for the KaushalTwin RPL platform.\n\n"
        "Provides skill extraction, NOS mapping, competency scoring, "
        "evidence analysis, and adaptive task selection for the first 5 modules.\n\n"
        "**IMPORTANT**: This service assists human assessors. "
        "It never certifies a worker and never produces final Commit/Abstain decisions."
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
