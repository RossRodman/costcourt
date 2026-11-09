"""Aggregates every route module under the `/api` prefix."""

from fastapi import APIRouter

from app.api.routes import health
from app.debate.router import router as debates_router
from app.estimates.router import router as estimates_router
from app.reports.router import router as reports_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(estimates_router)
api_router.include_router(debates_router)
api_router.include_router(reports_router)
