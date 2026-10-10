"""
KaushalTwin Backend — API Router: v1 prefix aggregation
"""

from fastapi import APIRouter

from app.api.v1 import auth, workers, evidence, assessments, ml

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workers.router)
api_router.include_router(evidence.router)
api_router.include_router(assessments.router)
api_router.include_router(ml.router)
